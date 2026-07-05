#ALB(Multi-AZ)
resource "aws_lb" "alb" {
  name               = "app-alb"
  load_balancer_type = "application"
  internal           = false

  security_groups = [aws_security_group.alb_sg.id]
  subnets         = aws_subnet.public_subnets[*].id
}

#Listener
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.alb.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.tg.arn
  }
}


#Launch template
resource "aws_launch_template" "app" {
  name_prefix   = "app-"
  image_id      = data.aws_ami.amazon_linux.id
  instance_type = "t2.micro"

  vpc_security_group_ids = [aws_security_group.app_sg.id]

  user_data = base64encode(file("userdata.sh"))
}


#Auto Scaling group
resource "aws_autoscaling_group" "asg" {
  desired_capacity    = 2
  max_size            = 4
  min_size            = 2
  vpc_zone_identifier = aws_subnet.private_subnets[*].id

  launch_template {
    id      = aws_launch_template.app.id
    version = "$Latest"
  }

  target_group_arns = [aws_lb_target_group.tg.arn]

  health_check_type = "ELB"
}