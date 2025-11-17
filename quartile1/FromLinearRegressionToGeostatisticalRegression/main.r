##### Regression Modelling and Analysis #####

### Load the required libraries ####
library(sf)
library(raster)
library(sp)
library(spdep)
library(gridExtra)
library(cowplot)

### Load and organize the data ######
setwd("C:/Users/darey/OneDrive/Documents/MGEO/MGEO/FromLinearRegressionToGeostatisticalRegression/Data")  # Set the working directory

rain.DF <- read.table("sic_obs.dat", sep = ",", header = T)  # Read data table

## Promote table to spatial data by assigning coordinates
rain.SpDF <- rain.DF
coordinates(rain.SpDF) <- c("x_coor", "y_coor")

Boundary.sf <- st_read("Swiss_Bound.shp")  # Read the boundary data as sf object
Boundary.sp <- as(Boundary.sf, "Spatial")  # Convert the sf object to sp object

DEM <- raster("DEM.grd")   # Read DEM raster layer
NDVI <- raster("NDVI.grd") # Read NDVI raster layer

x1 <- extract(DEM, rain.SpDF, df = T)[, 2]   # Extract first independent variable
x2 <- extract(NDVI, rain.SpDF, df = T)[, 2]  # Extract second independent variable
y <- rain.SpDF@data$rain_mm                  # Extract dependent/response variable
X <- cbind(1, x1, x2)                        # Construct design matrix

## Add attributes to the SpatialDataFrame
rain.SpDF@data$y <- y
rain.SpDF@data$x1 <- x1
rain.SpDF@data$x2 <- x2

## Variance-covariance and correlation analysis
n = length(y)
y.star <- y - mean(y)
x1.star <- x1 - mean(x1)
x2.star <- x2 - mean(x2)
Z <- cbind(y.star, x1.star, x2.star)
Sigma.Z <- (t(Z) %*% Z) / (n - 1)
Sigma.Z

LM1 <- lm(y ~ x1 + x2)
summary(LM1)

# Add this line to compute predicted (fitted) values
y_cap <- predict(LM1)   # or equivalently: LM1$fitted.values

# Compute residuals (optional but useful)
e <- y - y_cap
### SSE, MSE, and RMSE ###
SSE <- t(y - y_cap) %*% (y - y_cap); SSE
SSE.Alt <- sum((y - y_cap)^2); SSE.Alt
SSE.Alt2 <- t(e) %*% e; SSE.Alt2
K <- 2
MSE <- SSE / (n - (K + 1)); MSE
RMSE <- sqrt(MSE); RMSE

CovBeta <- as.vector(MSE) * (solve(t(X) %*% X)); CovBeta
CovBeta.Alt <- vcov(LM1); CovBeta.Alt

##### Spatial Prediction #####
## Create grid for prediction ###
# GridPts <- SpatialPixels(SpatialPoints(coordinates(DEM)))
PredGridPts <- spsample(Boundary.sp, n = 200000, type = "regular")
gridded(PredGridPts) <- T

## Extract the independent variables for the prediction locations
x10 <- extract(DEM, PredGridPts, df = T)[, 2]
x20 <- extract(NDVI, PredGridPts, df = T)[, 2]

### First Approach ###
newdata <- data.frame(x1 = x10, x2 = x20)
y0 <- predict(LM1, newdata = newdata, se.fit = T, interval = "prediction")

### Convert predictions to spatial data
y0.Sp <- SpatialPixelsDataFrame(points = PredGridPts, data = data.frame(y0 = y0))
# y0.Sp <- y0.Sp[Boundary.sp, ]  # Subset grids within the Boundary

spplot(y0.Sp, zcol = "y0.fit.fit", main = "Spatial prediction of rainfall")
spplot(y0.Sp, zcol = "y0.se.fit", main = "Prediction standard errors of rainfall")

library(gstat)
library(gridExtra)

vgm.cloud.y <- variogram(y ~ 1, locations = rain.SpDF, cloud = T)
vgm.Emp.y <- variogram(y ~ 1, locations = rain.SpDF)
vgm.cloud.e <- variogram(e ~ 1, locations = rain.SpDF, cloud = T)
vgm.Emp.e <- variogram(e ~ 1, locations = rain.SpDF)

grid.arrange(
  plot(vgm.cloud.y, main = "Semi-variogram cloud of rainfall"),
  plot(vgm.Emp.y, main = "Empirical semi-variogram of rainfall"),
  plot(vgm.cloud.e, main = "Semi-variogram cloud of residuals"),
  plot(vgm.Emp.e, main = "Empirical semi-variogram of residuals")
)

## Fit Exponential, Gaussian, and Spherical semi-variogram Models for rainfall
vgmExp.y <- fit.variogram(vgm.Emp.y, model = vgm(15000, "Exp", 60000, nugget = 500))
vgmGau.y <- fit.variogram(vgm.Emp.y, model = vgm(15000, "Gau", 60000, nugget = 500))
vgmSph.y <- fit.variogram(vgm.Emp.y, model = vgm(15000, "Sph", 60000, nugget = 500))

grid.arrange(
  plot(vgm.Emp.y, vgmExp.y, main = "Exponential Model of the rainfall"),
  plot(vgm.Emp.y, vgmGau.y, main = "Gaussian Model of the rainfall"),
  plot(vgm.Emp.y, vgmSph.y, main = "Spherical Model of the rainfall"),
  nrow = 2, ncol = 2
)

## Fit Exponential, Gaussian, and Spherical semi-variogram Models for the residuals
vgmExp.e <- fit.variogram(vgm.Emp.e, model = vgm(8000, "Exp", 60000, nugget = 500))
vgmGau.e <- fit.variogram(vgm.Emp.e, model = vgm(8000, "Gau", 60000, nugget = 500))
vgmSph.e <- fit.variogram(vgm.Emp.e, model = vgm(8000, "Sph", 60000, nugget = 500))

grid.arrange(
  plot(vgm.Emp.e, vgmExp.e, main = "Exponential Model of the residuals"),
  plot(vgm.Emp.e, vgmGau.e, main = "Gaussian Model of the residuals"),
  plot(vgm.Emp.e, vgmSph.e, main = "Spherical Model of the residuals"),
  nrow = 2, ncol = 2
)

### Geostatistical regression #####
## vgmSph.e: we have already fitted a semi-variogram model for the residuals

### Compute the distances between the observation locations
DMat <- spDists(rain.SpDF)

## Convert the semi-variogram of the residuals to covariance: example spherical model
Sigma.ols1 <- variogramLine(vgmSph.e, dist_vector = DMat, covariance = T)

## Compute the first GLS coefficients
Beta.gls1 <- solve(t(X) %*% solve(Sigma.ols1) %*% X) %*% (t(X) %*% solve(Sigma.ols1) %*% y)

## Compute the first GLS residuals
e.gls1 <- y - (X %*% Beta.gls1)

### The Iterations ######
B.gls.ite <- matrix(nrow = 100, ncol = 3)

for(i in 1:100) {
  ## Compute and fit the semi-variogram for the GLS residuals
  vgm.Emp.gls1 <- variogram(e.gls1 ~ 1, locations = rain.SpDF, covariogram = F)
  vgmExp.gls1 <- fit.variogram(vgm.Emp.gls1, model = vgm(8000, "Sph", 60000, nugget = 500))
  ## Convert the semi-variogram to Covariance
  Sigma.gls1 <- variogramLine(vgmExp.gls1, dist_vector = DMat, covariance = T)
  ## Compute the next GLS coefficients
  B.gls.ite[i, ] <- solve(t(X) %*% solve(Sigma.gls1) %*% X) %*% (t(X) %*% solve(Sigma.gls1) %*% y)
  ## Compute the next GLS residuals
  e.gls1 <- y - (X %*% B.gls.ite[i, ])
}
B.gls <- B.gls.ite[100, ]  
### Plotting the iterations of the GLS coefficients
par(mfrow = c(2, 2))
ts.plot(B.gls.ite[,1], lwd = 5, col = "black", main = "GLS estimates of the intercept",
        xlab = "Iterations", ylab = "Intercepts")
abline(h = max(B.gls.ite[,1]), lwd = 2, col = "red", lty = 2)

ts.plot(B.gls.ite[,2], lwd = 5, col = "black", main = "GLS estimates of the elevation coefficient",
        xlab = "Iterations", ylab = "Slopes")
abline(h = min(B.gls.ite[,2]), lwd = 2, col = "red", lty = 2)

ts.plot(B.gls.ite[,3], lwd = 5, col = "black", main = "GLS estimates of the NDVI coefficient",
        xlab = "Iterations", ylab = "Slopes")
abline(h = min(B.gls.ite[,3]), lwd = 2, col = "red", lty = 2)

### GLS standard errors ####
# Compute the GLS residuals
e.gls <- y - (X %*% B.gls)
# Compute sum of squared error SSE
SSE.gls <- t(e.gls) %*% e.gls; SSE.gls
# Compute the mean square errors (MSE)
k <- 2  # number of independent variables
MSE.gls <- SSE.gls / (n - (k + 1)); MSE.gls
# Compute the root mean square errors (RMSE)
RMSE.gls <- sqrt(MSE.gls); RMSE.gls

# Compute the Variance-covariance matrix of the GLS residuals
vgm.Emp.gls <- variogram(e.gls ~ 1, locations = rain.SpDF, covariogram = F)
vgmExp.gls <- fit.variogram(vgm.Emp.gls, model = vgm(8000, "Sph", 60000, nugget = 500))
Sigma.gls <- variogramLine(vgmExp.gls, dist_vector = DMat, covariance = T)

# Compute Variance-covariance matrix of GLS coefficients
Sigma.Beta.Gls <- solve(t(X) %*% solve(Sigma.gls) %*% X)
Sigma.Beta.Gls

# The standard errors of the GLS coefficients
sqrt(diag(Sigma.Beta.Gls))

#### Geostatistical Prediction #####

## Ordinary Kriging
## Design a prediction grid, 20000 points, within the boundary of the study area
OK.GridPts <- spsample(Boundary.sp, n = 20000, type = "regular")
gridded(OK.GridPts) <- T

## Let’s use the exponential model for rainfall: vgmExp.y
OK.Rain <- krige(y ~ 1, locations = rain.SpDF, newdata = OK.GridPts, model = vgmExp.y)

grid.arrange(
  spplot(OK.Rain, zcol = "var1.pred", main = "OK Predictions of Rainfall"),
  spplot(OK.Rain, zcol = "var1.var", main = "OK Prediction Variances of Rainfall")
)

## Regression Kriging
# Variogram of the GLS residuals: the independent variables are stored in the design matrix X
vgm.Emp.RK <- variogram(y ~ x1 + x2, locations = rain.SpDF, covariogram = F)
RK.GridPts <- spsample(Boundary.sp, n = 20000, type = "regular")

## The new data frame should also contain the independent variables at the prediction location
RK.GridPtsDF <- SpatialPointsDataFrame(
  RK.GridPts,
  data.frame(
    x1 = extract(DEM, RK.GridPts, df = T)[,2],
    x2 = extract(NDVI, RK.GridPts, df = T)[,2]
  )
)
## Convert the SpatialPointsDataFrame to SpatialPixelsDataFrame
gridded(RK.GridPtsDF) <- T

### Compute Regression Kriging
RK.Rain <- krige(y ~ x1 + x2, locations = rain.SpDF, newdata = RK.GridPtsDF, model = vgmExp.y)

## Plot the predictions and prediction variance
grid.arrange(
  spplot(RK.Rain, zcol = "var1.pred", main = "RK Predictions of Rainfall"),
  spplot(RK.Rain, zcol = "var1.var", main = "RK Prediction Variances of Rainfall")
)

### Cross-validation #####
RK.Rain.CV <- krige.cv(y ~ x1 + x2, locations = rain.SpDF, model = vgmExp.y)

## Five-fold cross-validation
RK.Rain.5_CV <- krige.cv(y ~ x1 + x2, locations = rain.SpDF, model = vgmExp.y, nfold = 5)

### ME, MSE, and RMSE
ME.RK.Rain <- sum(RK.Rain.CV$residual) / length(RK.Rain.CV$residual)
MSE.RK.Rain <- sum((RK.Rain.CV$residual)^2) / length(RK.Rain.CV$residual)
RMSE.RK.Rain <- sqrt(MSE.RK.Rain); RMSE.RK.Rain

### The R²; proportion of explained variance
R2.RK.Rain <- 1 - var(RK.Rain.CV$residual) / var(rain.SpDF$y); R2.RK.Rain

### ===== Error metrics & comparison: OK vs RK =====

# 1) LOO cross-validation for Ordinary Kriging (uses the same variogram model vgmExp.y)
OK.Rain.CV <- krige.cv(y ~ 1, locations = rain.SpDF, model = vgmExp.y)

# 2) (Already computed above) LOO cross-validation for Regression Kriging:
# RK.Rain.CV <- krige.cv(y ~ x1 + x2, locations = rain.SpDF, model = vgmExp.y)

# 3) Helper to compute common metrics
cv_metrics <- function(cv_obj, y_obs) {
  res <- cv_obj$residual
  data.frame(
    ME   = mean(res),
    MAE  = mean(abs(res)),
    MSE  = mean(res^2),
    RMSE = sqrt(mean(res^2)),
    R2   = 1 - var(res) / var(y_obs)
  )
}

# 4) Build a side-by-side summary
err_OK <- cv_metrics(OK.Rain.CV, rain.SpDF$y)
err_RK <- cv_metrics(RK.Rain.CV, rain.SpDF$y)
err_summary <- rbind(OK = err_OK, RK = err_RK)

# 5) Show nicely rounded table
print(round(err_summary, 4))

# 6) Quick textual comparison (lower RMSE is better)
better <- if (err_summary["OK","RMSE"] < err_summary["RK","RMSE"]) "OK" else "RK"
cat(sprintf(
  "\nComparison:\n- OK RMSE = %.4f\n- RK RMSE = %.4f\n=> Lower RMSE: %s\n",
  err_summary["OK","RMSE"], err_summary["RK","RMSE"], better
))
