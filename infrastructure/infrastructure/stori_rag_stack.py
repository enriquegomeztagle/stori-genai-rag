import os
from pathlib import Path
from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_ecr_assets as ecr_assets,
    aws_elasticloadbalancingv2 as elbv2,
    aws_secretsmanager as secretsmanager,
    aws_iam as iam,
    aws_s3 as s3,
    aws_elasticache as elasticache,
    aws_efs as efs,
    RemovalPolicy,
)
from aws_cdk.aws_ecr_assets import Platform
from constructs import Construct


class StoriRagStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        vpc = ec2.Vpc(self, "StoriVpc", max_azs=2, nat_gateways=1)

        efs_security_group = ec2.SecurityGroup(
            self,
            "EfsSecurityGroup",
            vpc=vpc,
            description="Security group for EFS file system",
            allow_all_outbound=True,
        )

        efs_security_group.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(2049),
            description="Allow NFS access from ECS tasks",
        )

        efs_file_system = efs.FileSystem(
            self,
            "ChromaEfsFileSystem",
            vpc=vpc,
            security_group=efs_security_group,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            performance_mode=efs.PerformanceMode.GENERAL_PURPOSE,
            throughput_mode=efs.ThroughputMode.BURSTING,
            enable_automatic_backups=True,
            removal_policy=RemovalPolicy.RETAIN,
        )

        efs_access_point = efs_file_system.add_access_point(
            "ChromaAccessPoint",
            path="/chroma",
            create_acl=efs.Acl(
                owner_gid="1000",
                owner_uid="1000",
                permissions="755",
            ),
            posix_user=efs.PosixUser(
                gid="1000",
                uid="1000",
            ),
        )

        redis_subnet_group = elasticache.CfnSubnetGroup(
            self,
            "RedisSubnetGroup",
            description="Subnet group for Redis cluster",
            subnet_ids=[subnet.subnet_id for subnet in vpc.private_subnets],
        )

        redis_security_group = ec2.SecurityGroup(
            self,
            "RedisSecurityGroup",
            vpc=vpc,
            description="Security group for Redis cluster",
            allow_all_outbound=True,
        )

        redis_security_group.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(6379),
            description="Allow Redis access from ECS tasks",
        )

        redis_cluster = elasticache.CfnCacheCluster(
            self,
            "RedisCluster",
            cache_node_type="cache.t3.micro",
            engine="redis",
            num_cache_nodes=1,
            port=6379,
            vpc_security_group_ids=[redis_security_group.security_group_id],
            cache_subnet_group_name=redis_subnet_group.ref,
            engine_version="7.0",
        )

        redis_endpoint = f"redis://{redis_cluster.attr_redis_endpoint_address}:6379"

        rag_secret = secretsmanager.Secret.from_secret_name_v2(
            self, "RagBackendSecret", "stori/rag/backend"
        )

        cluster = ecs.Cluster(self, "StoriCluster", vpc=vpc, container_insights=True)

        project_root = Path(__file__).resolve().parents[2]
        backend_asset = ecr_assets.DockerImageAsset(
            self,
            "BackendImage",
            directory=str(project_root / "backend"),
            platform=Platform.LINUX_AMD64,
        )

        frontend_asset = ecr_assets.DockerImageAsset(
            self,
            "FrontendImage",
            directory=str(project_root / "frontend"),
            platform=Platform.LINUX_AMD64,
        )

        efs_volume = ecs.Volume(
            name="chroma-efs-volume",
            efs_volume_configuration=ecs.EfsVolumeConfiguration(
                file_system_id=efs_file_system.file_system_id,
                transit_encryption="ENABLED",
                authorization_config=ecs.AuthorizationConfig(
                    access_point_id=efs_access_point.access_point_id,
                    iam="ENABLED",
                ),
            ),
        )

        backend = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "BackendService",
            cluster=cluster,
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_docker_image_asset(backend_asset),
                container_port=8000,
                environment={
                    "AWS_REGION": Stack.of(self).region,
                    "APP_NAME": "Stori GenAI RAG",
                    "APP_VERSION": "1.0.0",
                    "DEBUG": "false",
                    "CHUNK_SIZE": "1000",
                    "CHUNK_OVERLAP": "200",
                    "TOP_K_RETRIEVAL": "5",
                    "CORS_ORIGINS": '["*"]',
                    "REDIS_URL": redis_endpoint,
                    "REDIS_DB": "0",
                    "CHROMA_PERSIST_DIRECTORY": "/chroma/chroma_db",
                    "LANG": "es_ES.UTF-8",
                    "LC_ALL": "es_ES.UTF-8",
                    "LANGUAGE": "es_ES:es",
                },
                secrets={
                    "BEDROCK_MODEL_ID": ecs.Secret.from_secrets_manager(
                        rag_secret, "BEDROCK_MODEL_ID"
                    ),
                    "S3_BUCKET_NAME": ecs.Secret.from_secrets_manager(
                        rag_secret, "S3_BUCKET_NAME"
                    ),
                    "EMBEDDING_MODEL": ecs.Secret.from_secrets_manager(
                        rag_secret, "EMBEDDING_MODEL"
                    ),
                    "DEFAULT_LANGUAGE": ecs.Secret.from_secrets_manager(
                        rag_secret, "DEFAULT_LANGUAGE"
                    ),
                },
            ),
            desired_count=1,
            cpu=512,
            memory_limit_mib=1024,
            public_load_balancer=True,
        )

        backend.task_definition.add_volume(
            name=efs_volume.name,
            efs_volume_configuration=efs_volume.efs_volume_configuration,
        )

        backend.task_definition.default_container.add_mount_points(
            ecs.MountPoint(
                container_path="/chroma",
                source_volume="chroma-efs-volume",
                read_only=False,
            )
        )

        backend.service.connections.allow_to(
            redis_security_group,
            ec2.Port.tcp(6379),
            "Allow backend to connect to Redis",
        )

        backend.task_definition.task_role.add_to_policy(
            iam.PolicyStatement(
                actions=["secretsmanager:GetSecretValue"],
                resources=[rag_secret.secret_arn],
            )
        )

        backend.task_definition.task_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:DeleteObject",
                    "s3:ListBucket",
                    "s3:GetBucketLocation",
                    "s3:CreateBucket",
                    "s3:PutBucketVersioning",
                    "s3:PutBucketEncryption",
                    "s3:PutBucketPolicy",
                    "s3:PutBucketPublicAccessBlock",
                    "s3:GetBucketVersioning",
                    "s3:GetBucketEncryption",
                    "s3:GetBucketPolicy",
                    "s3:GetBucketPublicAccessBlock",
                ],
                resources=[
                    "arn:aws:s3:::*",
                    "arn:aws:s3:::*/*",
                ],
            )
        )

        backend.task_definition.task_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonBedrockFullAccess")
        )

        backend.task_definition.task_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "elasticfilesystem:ClientMount",
                    "elasticfilesystem:ClientWrite",
                    "elasticfilesystem:ClientRootAccess",
                ],
                resources=[efs_file_system.file_system_arn],
            )
        )

        frontend = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "FrontendService",
            cluster=cluster,
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_docker_image_asset(frontend_asset),
                container_port=3000,
                environment={
                    "VITE_API_URL": f"http://{backend.load_balancer.load_balancer_dns_name}",
                },
            ),
            desired_count=1,
            cpu=256,
            memory_limit_mib=512,
            public_load_balancer=True,
        )

        CfnOutput(
            self,
            "FrontendURL",
            value=f"http://{frontend.load_balancer.load_balancer_dns_name}",
        )

        CfnOutput(
            self,
            "BackendURL",
            value=f"http://{backend.load_balancer.load_balancer_dns_name}",
        )

        CfnOutput(
            self,
            "RedisEndpoint",
            value=redis_endpoint,
            description="Redis endpoint for the application",
        )

        CfnOutput(
            self,
            "DocumentsBucketName",
            value="Bucket name from secrets (S3_BUCKET_NAME)",
            description="S3 bucket name is read from secrets at runtime",
        )

        CfnOutput(
            self,
            "EfsFileSystemId",
            value=efs_file_system.file_system_id,
            description="EFS File System ID for Chroma persistence",
        )

        CfnOutput(
            self,
            "EfsAccessPointId",
            value=efs_access_point.access_point_id,
            description="EFS Access Point ID for Chroma data",
        )

        CfnOutput(
            self,
            "ChromaPersistDirectory",
            value="/chroma/chroma_db",
            description="Chroma persistence directory path in containers",
        )
