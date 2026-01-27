/*
variable "instance_name" {
  description = "Value of the EC2 instance's Name tag."
  type        = string
  default     = "learn-terraform-hmm"
}

variable "instance_type" {
  description = "The EC2 instance's type."
  type        = string
  default     = "t3.micro"
}
*/

variable "lambda_function_name" {
  description = "Name of lambda function"
  type        = string
  default     = "terraform_lambda"
}

variable "repo_name" {
  description = "Name of repo"
  type        = string
  default     = "terraform_practice_repo"
}

variable "AWS_account_id" {
  description = "AWS account ID"
  type        = string
  default     = "542726313726"

}

variable "AWS_region" {
  description = "AWS region"
  type        = string
  default     = "ap-southeast-2"

}

variable "use_image_tag" {
  description = "Controls whether to use image tag in ECR repository URI or not. Disable this to deploy latest image using ID (sha256:...)"
  type        = bool
  default     = true
}
