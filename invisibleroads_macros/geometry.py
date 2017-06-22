from copy import copy


def transform_geometries(geometries, f):
    transformed_geometries = []
    for geometry in geometries:
        if hasattr(geometry, 'geoms'):
            transformed_geometry = geometry.__class__(transform_geometries(
                geometry.geoms, f))
        else:
            transformed_geometry = copy(geometry)
            transformed_geometry.coords = [f(xyz) for xyz in geometry.coords]
        transformed_geometries.append(transformed_geometry)
    return transformed_geometries


def flip_xy(xyz):
    'Flip x and y coordinates whether or not there is a z-coordinate'
    xyz = list(xyz)  # Preserve original
    xyz[0], xyz[1] = xyz[1], xyz[0]
    return tuple(xyz)


def drop_z(xyz):
    return xyz[:2]
