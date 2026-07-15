output "network" {
  value = {
    vpc_id           = aws_vpc.my_vpc.id
    public_subnets   = aws_subnet.public_subnets[*].id
    private_subnets  = aws_subnet.private_subnets[*].id
  }
}

output "public_subnets" {
  value = aws_subnet.public_subnets[*].id
}


output "private_subnets" {
  value = aws_subnet.private_subnets[*].id
}


output "public_subnet_az_map" {
  value = zipmap(
    aws_subnet.public_subnets[*].id,
    aws_subnet.public_subnets[*].availability_zone
  )
}