#####Regression Modelling and Analysis #####
### Load the required libraries ####
#install.packages(c("sf", "raster", "sp", "spdep", "gridExtra", "cowplot"))

#####Regression Modelling and Analysis #####
### Load the required libraries ####
library(sf)
library(raster)
library(sp)
library(spdep)
library(gridExtra)
library(cowplot)
### Load and organize the data ######
setwd("C:\\Users\\darey\\OneDrive\\Documents\\Data_exercise1R")# Set the working directory
rain.DF <- read.table("sic_obs.dat", sep = ",", header = T)# Read data table
## Promote table to spatial data by assigning coordinates
rain.SpDF <- rain.DF
coordinates(rain.SpDF) <- c("x_coor","y_coor")
Boundary.sf <- st_read("Swiss_Bound.shp")## Read the boundary data as sf object
Boundary.sp <- as(Boundary.sf, "Spatial")## Conver the sf object to sp object
DEM <- raster("DEM.grd")## Read DEM raster layer
NDVI <- raster("NDVI.grd")## Read NDVI raster layer 3
x1 <- extract(DEM, rain.SpDF, df = T)[,2]## Extract first independentvariable
x2 <- extract(NDVI, rain.SpDF, df = T)[,2]# Extract second independent variable
y <- rain.SpDF@data$rain_mm # Extract dependent/ response variable
X <- cbind(1, x1, x2)## Construct design matrix
## Add attributes to the SpatialDataFrame
rain.SpDF@data$y <- y
rain.SpDF@data$x1 <- x1
rain.SpDF@data$x2 <- x2








