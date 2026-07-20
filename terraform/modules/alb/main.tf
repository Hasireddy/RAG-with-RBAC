#AlB(Multi-AZ)
resource "aws_lb" "alb"{
  name = "${var.name_prefix}-alb"
  load_balancer_type = "application"
  internal = false
  subnets = var.public_subnet_ids
  security_groups = [var.alb_sg_id]
  tags = {
    Name = "${var.name_prefix}-alb"
  }
}

#target group
resource "aws_lb_target_group" "tg" {
  name     = "${var.name_prefix}-tg"
  port     = var.app_port
  protocol = "HTTP"
  vpc_id   = var.vpc_id

  health_check {
    path                = var.health_check_path
    protocol            = "HTTP"
    matcher             = "200"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 2
  }
  tags = {
    Name = "${var.name_prefix}-tg"
  }
}

#Listener
resource "aws_lb_listener" "http"{
  load_balancer_arn = aws_lb.alb.arn
  port = 80
  protocol = "HTTP"

  default_action{
    type = "forward"
    target_group_arn = aws_lb_target_group.tg.arn
  }
}

