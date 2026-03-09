terraform {
  required_version = ">= 1.5"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
}

provider "aws" {
  region = var.aws_region
}

data "aws_caller_identity" "current" {}

# SQS Queue for Async Job Processing

resource "aws_sqs_queue" "analysis_jobs" {
  name                       = "stratos-analysis-jobs"
  delay_seconds             = 0
  max_message_size          = 262144
  message_retention_seconds = 86400  
  receive_wait_time_seconds = 10   
  visibility_timeout_seconds = 910   
  
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.analysis_jobs_dlq.arn
    maxReceiveCount     = 3
  })
  
  tags = {
    Project = "stratos"
    Part    = "6"
  }
}

resource "aws_sqs_queue" "analysis_jobs_dlq" {
  name = "stratos-analysis-jobs-dlq"
  
  tags = {
    Project = "stratos"
    Part    = "6"
  }
}

# IAM Role for Lambda Functions

resource "aws_iam_role" "lambda_agents_role" {
  name = "stratos-lambda-agents-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
  
  tags = {
    Project = "stratos"
    Part    = "6"
  }
}

# IAM policy for Lambda agents
resource "aws_iam_role_policy" "lambda_agents_policy" {
  name = "stratos-lambda-agents-policy"
  role = aws_iam_role.lambda_agents_role.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:*"
      },
      # SQS access for orchestrator
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = aws_sqs_queue.analysis_jobs.arn
      },
      # Lambda invocation for orchestrator to call other agents
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = "arn:aws:lambda:${var.aws_region}:${data.aws_caller_identity.current.account_id}:function:stratos-*"
      },
      # Aurora Data API access
      {
        Effect = "Allow"
        Action = [
          "rds-data:ExecuteStatement",
          "rds-data:BatchExecuteStatement",
          "rds-data:BeginTransaction",
          "rds-data:CommitTransaction",
          "rds-data:RollbackTransaction"
        ]
        Resource = var.aurora_cluster_arn
      },
      # Secrets Manager for database credentials
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = var.aurora_secret_arn
      },
      # S3 Vectors access for all agents
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::${var.vector_bucket}",
          "arn:aws:s3:::${var.vector_bucket}/*"
        ]
      },
      # S3 Vectors API access for all agents
      {
        Effect = "Allow"
        Action = [
          "s3vectors:QueryVectors",
          "s3vectors:GetVectors"
        ]
        Resource = "arn:aws:s3vectors:${var.aws_region}:${data.aws_caller_identity.current.account_id}:bucket/${var.vector_bucket}/index/*"
      },
      # SageMaker endpoint access for reporter agent
      {
        Effect = "Allow"
        Action = [
          "sagemaker:InvokeEndpoint"
        ]
        Resource = "arn:aws:sagemaker:${var.aws_region}:${data.aws_caller_identity.current.account_id}:endpoint/${var.sagemaker_endpoint}"
      },
      # Bedrock access for all agents
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream"
        ]
        Resource = [
          "arn:aws:bedrock:${var.bedrock_region}::foundation-model/*",
          "arn:aws:bedrock:${var.bedrock_region}:*:inference-profile/*"
        ]
      }
    ]
  })
}

# Attach basic Lambda execution role
resource "aws_iam_role_policy_attachment" "lambda_agents_basic" {
  role       = aws_iam_role.lambda_agents_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# S3 Bucket for Lambda Deployments

resource "aws_s3_bucket" "lambda_packages" {
  bucket = "stratos-lambda-packages-${data.aws_caller_identity.current.account_id}"
  
  tags = {
    Project = "stratos"
    Part    = "6"
  }
}

resource "aws_s3_object" "lambda_packages" {
  for_each = toset(["planner", "tagger", "reporter", "charter", "retirement"])
  
  bucket = aws_s3_bucket.lambda_packages.id
  key    = "${each.key}/${each.key}_lambda.zip"
  source = "${path.module}/../../backend/${each.key}/${each.key}_lambda.zip"
  etag   = fileexists("${path.module}/../../backend/${each.key}/${each.key}_lambda.zip") ? filemd5("${path.module}/../../backend/${each.key}/${each.key}_lambda.zip") : null
  
  tags = {
    Project = "stratos"
    Part    = "6"
    Agent   = each.key
  }
}

# Lambda Functions for Each Agent

resource "aws_lambda_function" "planner" {
  function_name = "stratos-planner"
  role          = aws_iam_role.lambda_agents_role.arn
  
  s3_bucket        = aws_s3_bucket.lambda_packages.id
  s3_key           = aws_s3_object.lambda_packages["planner"].key
  source_code_hash = fileexists("${path.module}/../../backend/planner/planner_lambda.zip") ? filebase64sha256("${path.module}/../../backend/planner/planner_lambda.zip") : null
  
  handler     = "lambda_handler.lambda_handler"
  runtime     = "python3.12"
  timeout     = 900 
  memory_size = 2048
  
  environment {
    variables = {
      AURORA_CLUSTER_ARN = var.aurora_cluster_arn
      AURORA_SECRET_ARN  = var.aurora_secret_arn
      DATABASE_NAME      = "stratos"
      VECTOR_BUCKET      = var.vector_bucket
      BEDROCK_MODEL_ID   = var.bedrock_model_id
      BEDROCK_REGION     = var.bedrock_region
      DEFAULT_AWS_REGION = var.aws_region
      SAGEMAKER_ENDPOINT = var.sagemaker_endpoint
      MASSIVE_API_KEY    = var.massive_api_key
      MASSIVE_PLAN       = var.massive_plan
      # LangFuse observability (optional)
      LANGFUSE_PUBLIC_KEY = var.langfuse_public_key
      LANGFUSE_SECRET_KEY = var.langfuse_secret_key
      LANGFUSE_HOST       = var.langfuse_host
      OPENAI_API_KEY      = var.openai_api_key
    }
  }

  tags = {
    Project = "stratos"
    Part    = "6"
    Agent   = "orchestrator"
  }
  
  depends_on = [aws_s3_object.lambda_packages["planner"]]
}

# SQS trigger for Planner
resource "aws_lambda_event_source_mapping" "planner_sqs" {
  event_source_arn = aws_sqs_queue.analysis_jobs.arn
  function_name    = aws_lambda_function.planner.arn
  batch_size       = 1
}

# Tagger Lambda
resource "aws_lambda_function" "tagger" {
  function_name = "stratos-tagger"
  role          = aws_iam_role.lambda_agents_role.arn

  # Using S3 for deployment package (>50MB)
  s3_bucket        = aws_s3_bucket.lambda_packages.id
  s3_key           = aws_s3_object.lambda_packages["tagger"].key
  source_code_hash = fileexists("${path.module}/../../backend/tagger/tagger_lambda.zip") ? filebase64sha256("${path.module}/../../backend/tagger/tagger_lambda.zip") : null

  handler     = "lambda_handler.lambda_handler"
  runtime     = "python3.12"
  timeout     = 300 
  memory_size = 1024

  environment {
    variables = {
      AURORA_CLUSTER_ARN = var.aurora_cluster_arn
      AURORA_SECRET_ARN  = var.aurora_secret_arn
      DATABASE_NAME      = "stratos"
      BEDROCK_MODEL_ID   = var.bedrock_model_id
      BEDROCK_REGION     = var.bedrock_region
      DEFAULT_AWS_REGION = var.aws_region
      LANGFUSE_PUBLIC_KEY = var.langfuse_public_key
      LANGFUSE_SECRET_KEY = var.langfuse_secret_key
      LANGFUSE_HOST       = var.langfuse_host
      OPENAI_API_KEY      = var.openai_api_key
    }
  }
  
  tags = {
    Project = "stratos"
    Part    = "6"
    Agent   = "tagger"
  }
  
  depends_on = [aws_s3_object.lambda_packages["tagger"]]
}

resource "aws_lambda_function" "reporter" {
  function_name = "stratos-reporter"
  role          = aws_iam_role.lambda_agents_role.arn
  
  s3_bucket        = aws_s3_bucket.lambda_packages.id
  s3_key           = aws_s3_object.lambda_packages["reporter"].key
  source_code_hash = fileexists("${path.module}/../../backend/reporter/reporter_lambda.zip") ? filebase64sha256("${path.module}/../../backend/reporter/reporter_lambda.zip") : null
  
  handler     = "lambda_handler.lambda_handler"
  runtime     = "python3.12"
  timeout     = 300  # 5 minutes for reporter agent
  memory_size = 1024
  
  environment {
    variables = {
      AURORA_CLUSTER_ARN = var.aurora_cluster_arn
      AURORA_SECRET_ARN  = var.aurora_secret_arn
      DATABASE_NAME      = "stratos"
      BEDROCK_MODEL_ID   = var.bedrock_model_id
      BEDROCK_REGION     = var.bedrock_region
      DEFAULT_AWS_REGION = var.aws_region
      SAGEMAKER_ENDPOINT = var.sagemaker_endpoint
      LANGFUSE_PUBLIC_KEY = var.langfuse_public_key
      LANGFUSE_SECRET_KEY = var.langfuse_secret_key
      LANGFUSE_HOST       = var.langfuse_host
      OPENAI_API_KEY      = var.openai_api_key
    }
  }

  tags = {
    Project = "stratos"
    Part    = "6"
    Agent   = "reporter"
  }
  
  depends_on = [aws_s3_object.lambda_packages["reporter"]]
}

resource "aws_lambda_function" "charter" {
  function_name = "stratos-charter"
  role          = aws_iam_role.lambda_agents_role.arn
  
  s3_bucket        = aws_s3_bucket.lambda_packages.id
  s3_key           = aws_s3_object.lambda_packages["charter"].key
  source_code_hash = fileexists("${path.module}/../../backend/charter/charter_lambda.zip") ? filebase64sha256("${path.module}/../../backend/charter/charter_lambda.zip") : null
  
  handler     = "lambda_handler.lambda_handler"
  runtime     = "python3.12"
  timeout     = 300 
  memory_size = 1024
  
  environment {
    variables = {
      AURORA_CLUSTER_ARN = var.aurora_cluster_arn
      AURORA_SECRET_ARN  = var.aurora_secret_arn
      DATABASE_NAME      = "stratos"
      BEDROCK_MODEL_ID   = var.bedrock_model_id
      BEDROCK_REGION     = var.bedrock_region
      DEFAULT_AWS_REGION = var.aws_region
      # LangFuse observability (optional)
      LANGFUSE_PUBLIC_KEY = var.langfuse_public_key
      LANGFUSE_SECRET_KEY = var.langfuse_secret_key
      LANGFUSE_HOST       = var.langfuse_host
      OPENAI_API_KEY      = var.openai_api_key
    }
  }

  tags = {
    Project = "stratos"
    Part    = "6"
    Agent   = "charter"
  }
  
  depends_on = [aws_s3_object.lambda_packages["charter"]]
}

resource "aws_lambda_function" "retirement" {
  function_name = "stratos-retirement"
  role          = aws_iam_role.lambda_agents_role.arn
  
  s3_bucket        = aws_s3_bucket.lambda_packages.id
  s3_key           = aws_s3_object.lambda_packages["retirement"].key
  source_code_hash = fileexists("${path.module}/../../backend/retirement/retirement_lambda.zip") ? filebase64sha256("${path.module}/../../backend/retirement/retirement_lambda.zip") : null
  
  handler     = "lambda_handler.lambda_handler"
  runtime     = "python3.12"
  timeout     = 300  
  memory_size = 1024
  
  environment {
    variables = {
      AURORA_CLUSTER_ARN = var.aurora_cluster_arn
      AURORA_SECRET_ARN  = var.aurora_secret_arn
      DATABASE_NAME      = "stratos"
      BEDROCK_MODEL_ID   = var.bedrock_model_id
      BEDROCK_REGION     = var.bedrock_region
      DEFAULT_AWS_REGION = var.aws_region
      LANGFUSE_PUBLIC_KEY = var.langfuse_public_key
      LANGFUSE_SECRET_KEY = var.langfuse_secret_key
      LANGFUSE_HOST       = var.langfuse_host
      OPENAI_API_KEY      = var.openai_api_key
    }
  }

  tags = {
    Project = "stratos"
    Part    = "6"
    Agent   = "retirement"
  }
  
  depends_on = [aws_s3_object.lambda_packages["retirement"]]
}

resource "aws_cloudwatch_log_group" "agent_logs" {
  for_each = toset(["planner", "tagger", "reporter", "charter", "retirement"])
  
  name              = "/aws/lambda/stratos-${each.key}"
  retention_in_days = 7
  
  tags = {
    Project = "stratos"
    Part    = "6"
    Agent   = each.key
  }
}