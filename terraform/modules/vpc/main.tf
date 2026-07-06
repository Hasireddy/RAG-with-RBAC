#Input variable for vpc
resource "aws_vpc" "my_vpc"{
  cidr_block = var.cidr_block
  enable_dns_hostnames = true
  enable_dns_support = true

  tags = {
    Name = "rag-vpc"
  }
}


#Availbility zones
data "aws_availability_zones" "azs" {
  state = "available"
}


#Value for Internet Gateway
resource "aws_internet_gateway" "my_igw"{
  vpc_id = aws_vpc.my_vpc.id

  tags = {
    Name = "my-igw"
  }
}


#Elastic ip
resource "aws_eip" "eip"{
  depends_on = [aws_internet_gateway.my_igw]
  domain = "vpc"

  tags = {
    Name = "elastic-ip"
  }
}


# NAT Gateway(for private subnets)
resource "aws_nat_gateway" "nat_gw"{
  allocation_id = aws_eip.eip.id
  subnet_id = aws_subnet.public_subnets[0].id
  depends_on = [aws_internet_gateway.my_igw]

  tags = {
    Name = "nat-gateway"
  }
}


#Input variable for the public subnet
resource "aws_subnet" "public_subnets"{
  count = var.public_subnets_count
  vpc_id = aws_vpc.my_vpc.id
  cidr_block = cidrsubnet(var.cidr_block, 8, count.index)
  availability_zone = data.aws_availability_zones.azs.names[count.index]
  map_public_ip_on_launch = true
  tags = {
    Name = "public-${data.aws_availability_zones.azs.names[count.index]}"
  }
}


#private subnet values
resource "aws_subnet" "private_subnets" {
  count = var.private_subnets_count
  vpc_id = aws_vpc.my_vpc.id
  cidr_block =  cidrsubnet(var.cidr_block, 8, count.index + var.public_subnets_count)
  availability_zone = data.aws_availability_zones.azs.names[count.index]
  map_public_ip_on_launch = false
  tags = {
    Name = "private-${data.aws_availability_zones.azs.names[count.index]}"
  }
}


#Value for route table
resource "aws_route_table" "public_rt"{
   vpc_id = aws_vpc.my_vpc.id
   route{
      cidr_block = "0.0.0.0/0"
     gateway_id = aws_internet_gateway.my_igw.id

   }

  tags = {
    Name = "public-rt"
  }
}


#private route table to route ec2 private subnet outbound traffic through NAT Gateway
resource "aws_route_table" "private_rt"{
   vpc_id = aws_vpc.my_vpc.id
   route{
      cidr_block = "0.0.0.0/0"
      nat_gateway_id = aws_nat_gateway.nat_gw.id

   }
  tags = {
    Name = "private-rt"
  }
}

#public subnet route table association
resource "aws_route_table_association" "public_rt_assoc"{
  count = var.public_subnets_count
  subnet_id = aws_subnet.public_subnets[count.index].id
  route_table_id = aws_route_table.public_rt.id
}


#private subnet route association
resource "aws_route_table_association" "app_rt_assoc"{
  count = var.private_subnets_count
  subnet_id = aws_subnet.private_subnets[count.index].id
  route_table_id = aws_route_table.private_rt.id
}