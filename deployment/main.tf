provider "aws" {
  region = var.AWS_region
}

data "aws_ecr_authorization_token" "token" {}

provider "docker" {
  registry_auth {
    address  = "${var.AWS_account_id}.dkr.ecr.${var.AWS_region}.amazonaws.com"
    username = data.aws_ecr_authorization_token.token.user_name
    password = data.aws_ecr_authorization_token.token.password
  }
}

module "lambda_function" {
  source = "terraform-aws-modules/lambda/aws"

  function_name  = var.lambda_function_name
  create_package = false

  image_uri    = module.docker_image.image_uri
  package_type = "Image"
}

module "docker_image" {
  source = "terraform-aws-modules/lambda/aws//modules/docker-build"

  create_ecr_repo = true
  ecr_repo        = var.repo_name

  use_image_tag = false
  #   image_tag     = "1.0"

  source_path = ".."
  build_args = {
    FOO = "bar"
  }
}
