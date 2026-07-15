#AlB(Multi-AZ)
resource "aws_lb" "alb"{
  name = "app-alb-new"
  load_balancer_type = "application"
  internal = false
  subnets = var.public_subnet_ids
  security_groups = [var.alb_sg_id]
}

#target group
resource "aws_lb_target_group" "tg"{
  name = "app-tg"
  port = 8000
  protocol = "HTTP"
  vpc_id = var.vpc_id

  health_check {
  path                = "/"
  protocol            = "HTTP"
  matcher             = "200"
  interval            = 30
  timeout             = 5
  healthy_threshold   = 2
  unhealthy_threshold = 2
  }
  tags = {
    Name = "app-tg"
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

