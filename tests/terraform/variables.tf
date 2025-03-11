variable "account_id" {
  description = "The id of the account on which the SAM application will be deployed"
  type        = string
}

variable "region" {
  type        = string
  description = "The AWS region in which to create resources"
}

variable "name" {
  type        = string
  description = "The name of the application"
}

variable "stack_name" {
  type        = string
  description = "The name of the stack used by SAM to store cloudformation templates"
}

variable "source_bucket_name" {
  type        = string
  description = "The name of the bucket used by SAM. This bucket will be created"
}
