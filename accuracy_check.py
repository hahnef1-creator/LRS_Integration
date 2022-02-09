import arcpy
import pandas as pd
import numpy
import geo
from statistics import mean
import time
from scipy.spatial import KDTree


def main():
    full_start = time.time()
    geodatabase = r"C:\Users\hahnef\Documents\ArcGIS\Projects\LRS_Test\LRS_Test.gdb"

    arcpy.env.workspace = geodatabase
    arcpy.env.OverwriteOutput= True
    arcpy.env.outputCoordinateSystem = arcpy.SpatialReference(4326)



    # read in gtfs layer as a pandas data frame. add a column and grab it's shape
    gtfs = geo.create_df(geodatabase,"leaz","SHAPE@")
    gtfs = gtfs[gtfs["LRS_ID"]!="off_network"]
    gtfs = gtfs.reset_index()
    num_rows_gtfs = gtfs.shape[0]

    # read in lrs joined point layer as a pandas dataframe. copy it. and turn the coords into float
    lrs_layer = geo.create_df_reproject(geodatabase,'state_n_local_point','SHAPE@',4326)
    lrs_layer_copy = lrs_layer.copy(deep=True)
    lrs_layer_copy['HUND_LATITUDE'] = lrs_layer_copy['HUND_LATITUDE'].astype(float)
    lrs_layer_copy['HUND_LONGITUDE'] = lrs_layer_copy['HUND_LONGITUDE'].astype(float)
    lrs_lat = lrs_layer_copy["HUND_LATITUDE"].to_numpy()
    lrs_lon = lrs_layer_copy["HUND_LONGITUDE"].to_numpy()
    stack_dist = numpy.column_stack((lrs_lon,lrs_lat))
    tree = KDTree(stack_dist)

    count=0
    confidence = []
    the_shape = gtfs.shape[0]
    index = 0
    for item in gtfs.itertuples(index=False):
        if gtfs.at[index,"Shape_Length"]==0:
            pass
        else:
            geom = gtfs.at[index,"Shape"]
            for point in geom.getPart(0):
                gtfs_lon = point.X
                gtfs_lat = point.Y
                gtfs_point = numpy.array([gtfs_lon,gtfs_lat])
                dist, ind = tree.query(gtfs_point,k=1)
                lrs_shape = lrs_layer.at[ind,"Shape"].getPart(0)
                lrs_lat = lrs_shape.Y
                lrs_lon = lrs_shape.X
                mag = numpy.sqrt((lrs_lat-gtfs_lat)**2+(lrs_lon-gtfs_lon)**2)
                if mag == 0:
                    confidence.append(0)
                    count+=1
                    
                else:
                    confidence.append(1)

        print("on index",index,"of",the_shape)
        index+=1

    accuracy = count/len(confidence)

    print("This the lrs integration accuracy",accuracy)

    



main()