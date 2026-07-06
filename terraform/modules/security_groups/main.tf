#ALB security group
resource "aws_security_group" "app_sg" {
  name   = "rag-security-group"
  vpc_id = aws_vpc.my_vpc.id

  ingress {
    description = "Allow traffic from ALB"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    security_groups = [aws-security_group.alb_sg.id]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "app-sg"
  }
}
