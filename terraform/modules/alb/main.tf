#AlB(Multi-AZ)
resource "aws_lb" "alb"{
  name = "app-alb"
  load_balancer_type = "application"
  internal = false
  subnets = aws_subnet.public_subnets[*].id
  security_groups = [aws_security_group.alb_sg.id]
}

#target group
resource "aws_lb_target_group" "tg"{
  name = "app-tg"
  port = 8000
  protocol = "HTTP"
  vpc_id = aws_vpc.my_vpc.id

  health_check {
  path                = "/"
  protocol            = "HTTP"
  matcher             = "200"
  interval            = 30
  healthy_threshold   = 2
  unhealthy_threshold = 2
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

resource "aws_lb_target_group_attachment" "app" {
  count = 2
  target_group_arn = aws_lb_target_group.tg.arn
  target_id        = aws_instance.app[count.index].id
  port             = 8000
}