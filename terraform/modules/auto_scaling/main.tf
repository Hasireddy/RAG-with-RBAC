
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }

   filter {
     name = "architecture"
     values = ["x86_64"]
   }
}

#Launch template
resource "aws_launch_template" "app" {
  name_prefix   = "app-"
  image_id      = data.aws_ami.amazon_linux.id
  instance_type = "t2.micro"
  key_name = var.key_name

  user_data = base64encode(templatefile("${path.module}/userdata.sh.tftpl", {
    api_key         = var.api_key
  }))
  network_interfaces {
    associate_public_ip_address = true
    security_groups = [var.app_sg_id]
  }

  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required"
  }

  block_device_mappings {

    device_name = "/dev/xvda"

    ebs {
      encrypted   = true
      volume_size = 20
      volume_type = "gp3"
    }
  }
  iam_instance_profile { name = aws_iam_instance_profile.app_profile.name }
  tag_specifications {
    resource_type = "instance"

    tags = {
      Name = "app-instance"
    }
  }
}

resource "aws_iam_role" "app_role" {
  name = "app-instance-role"
  assume_role_policy = jsonencode({
      Version = "2012-10-17"
      Statement = [{
        Action = "sts:AssumeRole"
        Effect = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      }]
  })
}

resource "aws_iam_instance_profile" "app_profile" {
  name = "app-instance-profile"
  role = aws_iam_role.app_role.name
}

resource "aws_iam_role_policy_attachment" "ssm_access" {
  role       = aws_iam_role.app_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}


#Auto Scaling group
resource "aws_autoscaling_group" "asg" {
  desired_capacity    = 2
  max_size            = 4
  min_size            = 2
  vpc_zone_identifier = var.public_subnet_ids

  launch_template {
    id      = aws_launch_template.app.id
    version = "$Latest"
  }

    target_group_arns = [var.target_group_arn]

    health_check_type = "ELB"

    health_check_grace_period = 600

    instance_refresh {
    strategy = "Rolling"

    preferences {
      min_healthy_percentage = 50
    }
  }

    tag {
      key                 = "Name"
      value               = "app-instance"
      propagate_at_launch = true
    }
  }


resource "aws_autoscaling_policy" "cpu_scaling" {

  name                   = "cpu-scaling"
  autoscaling_group_name = aws_autoscaling_group.asg.name

  policy_type = "TargetTrackingScaling"

  target_tracking_configuration {

    predefined_metric_specification {
      predefined_metric_type = "ASGAverageCPUUtilization"
    }

    target_value = 70.0
  }
}

