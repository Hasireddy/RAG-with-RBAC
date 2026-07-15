variable "vpc_id"{

}

variable "public_subnet_ids" {
  description = "Public subnet IDs for Auto Scaling instances"
  type        = list(string)
}

variable "app_sg_id"{

}


variable "target_group_arn"{

}

 variable "key_name" {
     description = "EC2 key pair name for SSH access"
     type        = string
 }

variable "api_key" {
  type      = string
  sensitive = true
}