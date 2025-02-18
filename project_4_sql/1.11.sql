SELECT Products.Name, Price,Manufacturers.Name
FROM Products
JOIN Manufacturers
ON Products.Manufacturer = Manufacturers.Code