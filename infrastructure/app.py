import os
import aws_cdk as cdk
from infrastructure.stori_rag_stack import StoriRagStack

app = cdk.App()

StoriRagStack(
    app,
    "StoriRagStack",
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"), region=os.getenv("CDK_DEFAULT_REGION")
    ),
)

app.synth()
