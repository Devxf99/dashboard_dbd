import geopandas as gpd

# baca shapefile kecamatan indonesia
gdf = gpd.read_file("gadm41_IDN_3.shp")

# lihat nama kolom
print(gdf.columns)

# filter wilayah Kota Bima
bima = gdf[gdf["NAME_2"] == "Kota Bima"]

# simpan ke geojson
bima.to_file("kecamatan_bima.geojson", driver="GeoJSON")

print("Berhasil membuat kecamatan_bima.geojson")
