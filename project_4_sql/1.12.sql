# -- 1.12 Select the average price of each manufacturer's products, showing only the manufacturer's code.

SELECT avg(Price), Manufacturers.Code
FROM Products
JOIN Manufacturers
ON Products.Manufacturer = Manufacturers.Code
GROUP BY Manufacturers.Code