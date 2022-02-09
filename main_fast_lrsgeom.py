import arcpy
import pandas as pd
import numpy
import geo
import time
from scipy.spatial import KDTree

def main():
    full_start = time.time()
    geodatabase = r"C:\Users\hahnef\Documents\ArcGIS\Projects\LRS_Test\LRS_Test.gdb"

    arcpy.env.workspace = geodatabase
    arcpy.env.OverwriteOutput= True
    arcpy.env.outputCoordinateSystem = arcpy.SpatialReference(4326)

    # read in gtfs layer as a pandas data frame. add LRS_ID column and grab the number of rows
    gtfs = geo.create_df(geodatabase,"CTDOT_PublicTrans_Bus_GTFSBusRoutes","SHAPE@")
    gtfs["LRS_ID"]=None
    num_rows_gtfs = gtfs.shape[0]

    # read in lrs joined point layer as a pandas dataframe. copy it. and turn the coords into float
    lrs_layer = geo.create_df(geodatabase,'state_n_local_point','SHAPE@')
    lrs_layer_copy = lrs_layer.copy(deep=True)
    lrs_layer_copy['HUND_LATITUDE'] = lrs_layer_copy['HUND_LATITUDE'].astype(float)
    lrs_layer_copy['HUND_LONGITUDE'] = lrs_layer_copy['HUND_LONGITUDE'].astype(float)
    lrs_lat = lrs_layer_copy["HUND_LATITUDE"].to_numpy()
    lrs_lon = lrs_layer_copy["HUND_LONGITUDE"].to_numpy()
    # create the KDTree using the lat and lon coordinates
    stack_dist = numpy.column_stack((lrs_lon,lrs_lat))
    tree = KDTree(stack_dist)

    # create storage dictionary for all the output data
    adict = {i:[] for i in gtfs.columns}
    # create list of column names
    column_names = [i for i in gtfs.columns]
    
    index = 0
    # loop through the gtfs layer for each line
    for row in gtfs.itertuples(index=False):
        # grab the line info
        geom = gtfs.at[index,"Shape"]
       
        # initialize dictionary to store the geometry as the key and the lrs_id as the value
        line_info_dict={}
        # iterate through all the points that make up the line
        for point in geom.getPart(0):
            gtfs_lon = point.X
            gtfs_lat = point.Y
            # query the tree to find the closest lat and lon coordinate to the lrs layer
            gtfs_point = numpy.array([gtfs_lon,gtfs_lat])
            dist, ind = tree.query(gtfs_point,k=1)
            # grab closest geometry
            lrs_shape = lrs_layer_copy.at[ind,"Shape"].getPart(0)
            # create new point object for the lrs geometry
            lrs_point = arcpy.Point(lrs_shape.X,lrs_shape.Y)
            # create new point object for the original geometry
            point_with_m = arcpy.Point(gtfs_lon,gtfs_lat)
            lrs_pg= arcpy.PointGeometry(lrs_point,arcpy.SpatialReference(4326))
            gtfs_pg = arcpy.PointGeometry(point_with_m,arcpy.SpatialReference(4326))
            # grab matching lrs_id associated with the point
            lrs_id = lrs_layer_copy["ROUTE_ID"].iloc[ind]
            # find the distance in meters between the original point geom and lrs point geom
            a1,d1=lrs_pg.angleAndDistanceTo(gtfs_pg,'GEODESIC')
            # convert that distance to feet
            feet_dist = d1*3.28084

            # if the distance between the two points is greater than 100 feet. consider that as offnetwork and add it to the dictionary
            if feet_dist > 100:
                line_info_dict[point_with_m]="off_network"
            # otherwise use the lrs geometry and the matching lrs id
            else:
                line_info_dict[lrs_point]=lrs_id
      
        # create a list of all the values in the dictionary
        values = list(line_info_dict.values())
 
        # initialize a new dictionary to fix the intersection points
        new_line_info_dict = {}
        for key, value in line_info_dict.items():
            # if the lrs_id only appears once in the dictionary, its probabably an intersection. take all values greater than 1
            if values.count(value)>1:
                new_line_info_dict[key]=value
            # otherwise, change the lrs id to suspicious, will change later on in the process.
            else:
                new_line_info_dict[key]="sus"

        # separate dict into 2 lists (points and lrs_ids for indexing purposes)
        points = []
        lrs_ids = []
        for k, v in new_line_info_dict.items():
            points.append(k)
            lrs_ids.append(v)

        # if the lrs_id is labeled "sus". turn the value into the previous or later lrs_id
        for i in range(len(lrs_ids)):
            # accounts for condition of the first value, cant choose previous if the first value is sus
            if i == 0:
                # if the first value is sus. keep searching until one that isnt sus is found
                if lrs_ids[i] == "sus":
                    lrs_ids[i]=lrs_ids[i+1]
                    if lrs_ids[i+1] == "sus":
                        for j in range(len(lrs_ids)):
                            if lrs_ids[j] != "sus":
                                lrs_ids[i] = lrs_ids[j]
                                break
                else:
                    pass
            # if any value is sus. take the previous value as the true value
            elif lrs_ids[i]=="sus":
                lrs_ids[i]=lrs_ids[i-1]

        # make sure points doesnt have alternating values (cant have a line with only 1 point) turns in between value to outside value
        for i in range(len(lrs_ids)):
            if i == 0:
                pass
            elif i == len(lrs_ids)-1:
                if lrs_ids[len(lrs_ids)-1] != lrs_ids[i-1]:
                    lrs_ids[len(lrs_ids)-1]=lrs_ids[i-1]
            elif lrs_ids[i] != lrs_ids[i+1] and lrs_ids[i]!=lrs_ids[i-1]:
                lrs_ids[i]=lrs_ids[i-1]
        
        # if first index starts as alternating, change it to the next one
        if len(lrs_ids)>1 and lrs_ids[0]!=lrs_ids[1]:
            lrs_ids[0]=lrs_ids[1]

        # create list of lists for where the lrs_id's change aka each lrs id should be a line. 
        new_points = []
        new_lrs_ids = []
        change_count = 0
        for i in range(len(lrs_ids)):
            if lrs_ids[i]!=lrs_ids[i-1]:
                new_lrs_ids.append(lrs_ids[change_count:i])
                new_points.append(points[change_count:i])
                change_count = i
            elif i == len(lrs_ids)-1:
                new_lrs_ids.append(lrs_ids[change_count:i+1])
                new_points.append(points[change_count:i+1])
        if len(new_lrs_ids[0])==0:
            new_lrs_ids.pop(0)
            new_points.pop(0)

        # iterate over the list of lists and create lines and add the data to the dictionary
        for line in range(len(new_lrs_ids)):
            array = arcpy.Array()
            # for consistency. add the last point of the last line. makes it so all points connect.
            if line != 0:
                array.add(new_points[line-1][-1])
            # add the points to arcpy array
            for point in new_points[line]:
                array.add(point)
            # create line object and take lrs id
            polyline =arcpy.Polyline(array,arcpy.SpatialReference(4326))
            the_lrs_id = new_lrs_ids[line][0]
            # if sus still remains. it means there was a full line of "sus", meaning that it should be checked for review
            if the_lrs_id == "sus":
                the_lrs_id = "Check for Review" 
            # add all the data in the storage dictionary at the beginning. 
            for name in column_names:
                if name == "Shape":
                    adict["Shape"].append(polyline)
                elif name == "LRS_ID":

                    adict["LRS_ID"].append(the_lrs_id)
                else:
                    adict[name].append(getattr(row,name))
        

        print("ON INDEX",index, "OUT OF",num_rows_gtfs)
        
        index+=1
    
    # create new =dataframe from dictionary
    new_storage_df =pd.DataFrame(adict,columns=[i for i in gtfs.columns])
    # finally take the dataframe and add it to the geo database. 
    geo.add_df_to_dbase(geodatabase,"lrs_integrated_bus_routes_secondrun",new_storage_df,"POLYLINE")
    full_end = time.time()
    print("TIME:",full_end-full_start,"seconds")

  


main()