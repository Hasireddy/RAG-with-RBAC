# Ec2 instances
resource "aws_instance" "app"{
  count = var.private_subnets_count
  ami = data.aws_ami.amazon_linux.id
  instance_type = var.instance_type
  subnet_id = aws_subnet.private_subnets[count.index].id
  vpc_security_group_ids = [aws_security_group.app_sg.id]
  associate_public_ip_address = false

  tags = {
    Name = "app-${count.index + 1}"
  }
}

#AMI
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }
}