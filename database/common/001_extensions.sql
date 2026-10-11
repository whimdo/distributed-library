-- Enable the spatial extension in every database node.
CREATE EXTENSION IF NOT EXISTS postgis;

-- Print the installed version in the container initialization output.
SELECT PostGIS_Full_Version();
