-- 1.13 Select the average price of each manufacturer's products, showing the manufacturer's name.

SELECT avg(Price), Manufacturers.Name
FROM Products
JOIN Manufacturers
ON Products.Manufacturer = Manufacturers.Code
GROUP BY Manufacturers.Name