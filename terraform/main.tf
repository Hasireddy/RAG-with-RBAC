provider "aws" {
  region = "eu-central-1"
}

module "vpc" {
  source     = "./modules/vpc"
  cidr_block = "10.0.0.0/16"
}

module "security_groups" {
  source = "./modules/security_groups"
  vpc_id = module.vpc.network.vpc_id
}

module "alb" {
  source            = "./modules/alb"
  vpc_id            = module.vpc.network.vpc_id
  public_subnet_ids = module.vpc.network.public_subnets
  alb_sg_id         = module.security_groups.alb_sg_id
}

module "auto_scaling" {
  source            = "./modules/auto_scaling"
  vpc_id            = module.vpc.network.vpc_id
  public_subnet_ids = module.vpc.public_subnets
  app_sg_id         = module.security_groups.app_sg_id
  target_group_arn  = module.alb.target_group_arn
  key_name          = "rag-key"
  api_key           = var.api_key
}



