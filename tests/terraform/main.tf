terraform {
}

provider "aws" {
  region = var.region
}

module "service-scheduler" {
  source  = "epsilonline/sam-app-pipeline/aws"

  name = "demo"
  region = var.region
  account_id = var.region
  source_bucket_name = var.source_bucket_name
  stack_name = "service-scheduler"


  sam_cloudformation_variables = {
    Environment = "dev"
    ScheduleConfigTable = "lamiabellatabella"
    KMSArn = "arn:aws:kms:eu-west-1:xxx:key/23447391-502f-4df6-xxxx"
    ScheduleStatusTable="lamiabellatabella-status"
  }
}
