import arcpy
import pandas as pd
import numpy
import geo
from statistics import mean
import time
from scipy.spatial import KDTree

# maybe integrate if greater than some odd feet. label it as off network. otherwise label it sus
def main():
    full_start = time.time()
    geodatabase = r"C:\Users\hahnef\Documents\ArcGIS\Projects\LRS_Test\LRS_Test.gdb"

    arcpy.env.workspace = geodatabase
    arcpy.env.OverwriteOutput= True
    arcpy.env.outputCoordinateSystem = arcpy.SpatialReference(4326)

    # read in gtfs layer as a pandas data frame. add a column and grab it's shape
    gtfs = geo.create_df(geodatabase,"CTDOT_PublicTrans_Bus_GTFSBusRoutes","SHAPE@")
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

    #new_storage_df =pd.DataFrame(columns=[i for i in gtfs.columns])

    adict = {i:[] for i in gtfs.columns}
    column_names = [i for i in gtfs.columns]
    
    index = 0
    # loop through the gtfs layer for each line
    
    for row in gtfs.itertuples(index=False):
        # grab the line
        geom = gtfs.at[index,"Shape"]
        # iterate through all the points that make up the line
       
        array = arcpy.Array()
        for point in geom.getPart(0):
            gtfs_lon = point.X
            gtfs_lat = point.Y
            gtfs_point = numpy.array([gtfs_lon,gtfs_lat])
            dist, ind = tree.query(gtfs_point,k=1)
            lrs_shape = lrs_layer_copy.at[ind,"Shape"].getPart(0)
            lrs_point = arcpy.Point(lrs_shape.X,lrs_shape.Y)
            point_with_m = arcpy.Point(gtfs_lon,gtfs_lat)
            lrs_pg= arcpy.PointGeometry(lrs_point,arcpy.SpatialReference(4326))
            gtfs_pg = arcpy.PointGeometry(point_with_m,arcpy.SpatialReference(4326))
            lrs_id = lrs_layer_copy["ROUTE_ID"].iloc[ind]
            a1,d1=lrs_pg.angleAndDistanceTo(gtfs_pg,'GEODESIC')
            feet_dist = d1*3.28084
            if feet_dist > 100:
                array.add(point_with_m)
            else:
                array.add(lrs_point)
        polyline = arcpy.Polyline(array,arcpy.SpatialReference(4326))
        for name in column_names:
            if name == "Shape":
                adict["Shape"].append(polyline)
            else:
                adict[name].append(getattr(row,name))
        print("ON INDEX",index, "OUT OF",num_rows_gtfs)
        
        index+=1
      
    
    new_storage_df =pd.DataFrame(adict,columns=[i for i in gtfs.columns])
    # finally take the dataframe and add it to the geo database. 
    geo.add_df_to_dbase(geodatabase,"BUS_ROUTES_INTEGRATED_not_SEP",new_storage_df,"POLYLINE")
    full_end = time.time()
    print("TIME:",full_end-full_start,"seconds")

  


main()