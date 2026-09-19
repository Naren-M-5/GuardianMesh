# AWS target architecture

Planned competition deployment:

`API Gateway -> Lambda ingestion -> EventBridge -> processing Lambda -> DynamoDB -> AgentCore Runtime (Strands + Bedrock) -> GuardianMesh UI`

S3 is only for explicitly preserved evidence and uses encryption, least-privilege IAM, and lifecycle deletion. CloudWatch provides operational telemetry without logging raw webhook secrets or private media.

Before deployment, add infrastructure as code with separate dev/demo environments, budgets, scoped IAM roles, secret storage, DynamoDB access patterns, and teardown instructions. AWS services must execute in the submitted demo for the AWS Builder mini challenge.
