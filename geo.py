import pandas as pd
import arcpy
import numpy
import math

def getfieldnames(path):
    field_names = []
    fields = arcpy.ListFields(path)
    for field in fields:
        field_names.append(field.name)
    return field_names

def create_FC(workspace_path,pandas_table,fc_or_table_name,space_ref,geometry_type):
    arcpy.management.CreateFeatureclass(workspace_path, fc_or_table_name, geometry_type=geometry_type, has_m="DISABLED", 
                                        has_z="DISABLED", spatial_reference=space_ref,out_alias=fc_or_table_name)
    # check for what datatype to assign fields and create name based on pd df                                                           
    for i in pandas_table.columns:
        if i == "OBJECTID":
            pass
        elif i == "Shape":
            pass
        elif i == "Shape_Length":
            pass
        elif i == "M":
            arcpy.management.AddField(fc_or_table_name, field_name=i, field_type="DOUBLE")
        elif i == "shape_pt_lat":
            arcpy.management.AddField(fc_or_table_name, field_name=i, field_type="DOUBLE")
        elif i == "shape_pt_lon":
            arcpy.management.AddField(fc_or_table_name, field_name=i, field_type="DOUBLE")
        elif i == "stop_lat":
            arcpy.management.AddField(fc_or_table_name, field_name=i, field_type="DOUBLE")
        elif i == "stop_lon":
            arcpy.management.AddField(fc_or_table_name, field_name=i, field_type="DOUBLE")
        elif i == "Shape_Length":
            arcpy.management.AddField(fc_or_table_name, field_name=i, field_type="DOUBLE")
        elif i == "BEGIN_POINT":
            arcpy.management.AddField(fc_or_table_name, field_name=i, field_type="DOUBLE")
        elif i == "END_POINT":
            arcpy.management.AddField(fc_or_table_name, field_name=i, field_type="DOUBLE")
        else:
            arcpy.management.AddField(fc_or_table_name, field_name=i, field_type="TEXT")
def create_FC_Norm(workspace_path,names_list,fc_or_table_name,space_ref,geometry_type):
    arcpy.management.CreateFeatureclass(workspace_path, fc_or_table_name, geometry_type=geometry_type, has_m="DISABLED", 
                                        has_z="DISABLED", spatial_reference=space_ref,out_alias=fc_or_table_name)
    # check for what datatype to assign fields and create name based on pd df                                                           
    for i in names_list:
        if i == "OBJECTID":
            pass
        elif i == "Shape":
            pass
        elif i == "SHAPE@":
            pass
        elif i == "SHAPE@XY":
            pass
        elif i == "Shape_Length":
            pass
        elif i == "shape_pt_lat":
            arcpy.management.AddField(fc_or_table_name, field_name=i, field_type="DOUBLE")
        elif i == "shape_pt_lon":
            arcpy.management.AddField(fc_or_table_name, field_name=i, field_type="DOUBLE")
        elif i == "stop_lat":
            arcpy.management.AddField(fc_or_table_name, field_name=i, field_type="DOUBLE")
        elif i == "stop_lon":
            arcpy.management.AddField(fc_or_table_name, field_name=i, field_type="DOUBLE")
        elif i == "Shape_Length":
            arcpy.management.AddField(fc_or_table_name, field_name=i, field_type="DOUBLE")
        elif i == "BEGIN_POINT":
            arcpy.management.AddField(fc_or_table_name, field_name=i, field_type="DOUBLE")
        elif i == "END_POINT":
            arcpy.management.AddField(fc_or_table_name, field_name=i, field_type="DOUBLE")
        else:
            arcpy.management.AddField(fc_or_table_name, field_name=i, field_type="TEXT")

def add_df_to_dbase(geodatabase,desired_layer_name,pandas_df,geometry_type):
    print("adding " + desired_layer_name + " to "+ geodatabase)
    create_FC(geodatabase,pandas_df,desired_layer_name,arcpy.SpatialReference(4326),geometry_type)
    new_field_order = getfieldnames(geodatabase + '\\'+desired_layer_name)
    pandas_df = pandas_df.reindex(columns=new_field_order)
    count=0
    alist=[]
    shape_length_count = 0
    objectid_count = 0
    for col in pandas_df.columns:
        if col == "Shape":
            alist.append("Shape@")
        elif col == "Shape_Length":
            shape_length_count = count
            alist.append("Shape_Length")
        elif col == "OBJECTID":
            alist.append("OBJECTID")
        else:
            alist.append(col)
        count+=1
    cursor = arcpy.da.InsertCursor(desired_layer_name,alist)
    # create dynamic tuple for for insert row
    for row in pandas_df.itertuples():
        alist2 = []
        for i in range(count):
            if i == shape_length_count:
                alist2.append("filler")
            else:
                alist2.append(row[i+1])

        cursor.insertRow(tuple(alist2))
    del cursor

# geom type shape@, shapeXY etc...
def create_df(geodatabase,fc,geom_type):
    path = geodatabase + '\\'+ fc
    field_names = []
    fields = arcpy.ListFields(path)
    for field in fields:
        field_names.append(field.name)
    adict = {}
    for i in field_names:
        if i == "Shape":
            adict[i]=[row[0] for row in arcpy.da.SearchCursor(fc,geom_type)]
        else:
            adict[i]=[row[0] for row in arcpy.da.SearchCursor(fc,i)]

    df = pd.DataFrame(adict,columns=field_names)
    return df

def create_df_reproject(geodatabase,fc,geom_type,projection_num):
    path = geodatabase + '\\'+ fc
    field_names = []
    fields = arcpy.ListFields(path)
    for field in fields:
        field_names.append(field.name)
    adict = {}
    for i in field_names:
        if i == "Shape":
            adict[i]=[row[0].projectAs(arcpy.SpatialReference(projection_num)) for row in arcpy.da.SearchCursor(fc,geom_type)]
        else:
            adict[i]=[row[0] for row in arcpy.da.SearchCursor(fc,i)]

    df = pd.DataFrame(adict,columns=field_names)
    return df

def create_data_dict(geodatabase,fc,geom_type):
    path = geodatabase + '\\'+ fc
    field_names = []
    fields = arcpy.ListFields(path)
    for field in fields:
        field_names.append(field.name)
    adict = {}
    for i in field_names:
        if i == "Shape":
            adict[i]=[row[0] for row in arcpy.da.SearchCursor(fc,geom_type)]
        else:
            adict[i]=[row[0] for row in arcpy.da.SearchCursor(fc,i)]
    return adict

def get_distance_in_feet(lat1,lon1,lat2,lon2):
    R = 6378.137
    dLat = lat2 * numpy.pi / 180 - lat1 * numpy.pi / 180
    dLon = lon2 * numpy.pi / 180 - lon1 * numpy.pi / 180
    a = numpy.sin(dLat/2) * numpy.sin(dLat/2) + numpy.cos(lat1 * numpy.pi / 180) * numpy.cos(lat2 * numpy.pi / 180) *numpy.sin(dLon/2) * numpy.sin(dLon/2)
    c = 2 * math.atan(numpy.sqrt(a)/numpy.sqrt(1-a))
    d = R*c*1000 # d is in meters
    return d*3.2808399

def delete_small_length(geodatabase,fc,length):
    layer = geodatabase + '\\'+fc
    with arcpy.da.UpdateCursor(fc, "Shape_Length") as cursor:
        for row in cursor:
            if row[0] < length:
                print("deleting row of shape length",row[0])
                cursor.deleteRow()
