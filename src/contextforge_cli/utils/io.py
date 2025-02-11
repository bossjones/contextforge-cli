# pylint: disable=possibly-used-before-assignment
"""io.py"""

from __future__ import annotations

import csv
import os
import re
from glob import glob
from pathlib import Path

import numpy as np
from dask import array as da
from dask import delayed

from contextforge_cli.utils.misc import abspath_or_url


# SOURCE: https://github.com/napari/napari/blob/5f96d5d814aad697c367bdadbb1a57750e2114ad/napari/utils/io.py
def imread(filename: str) -> np.ndarray:
    """
    Custom implementation of imread to avoid skimage dependency.

    Parameters
    ----------
    filename : string
        The path from which to read the image.

    Returns
    -------
    data : np.ndarray
        The image data.

    """
    filename = abspath_or_url(filename)

    import imageio

    return imageio.imread(filename)


def _alphanumeric_key(s):
    """
    Convert string to list of strings and ints that gives intuitive sorting.

    Parameters
    ----------
    s : string

    Returns
    -------
    k : a list of strings and ints

    Examples
    --------
    >>> _alphanumeric_key("z23a")
    ['z', 23, 'a']
    >>> filenames = ["f9.10.png", "e10.png", "f9.9.png", "f10.10.png", "f10.9.png"]
    >>> sorted(filenames)
    ['e10.png', 'f10.10.png', 'f10.9.png', 'f9.10.png', 'f9.9.png']
    >>> sorted(filenames, key=_alphanumeric_key)
    ['e10.png', 'f9.9.png', 'f9.10.png', 'f10.9.png', 'f10.10.png']

    """
    return [int(c) if c.isdigit() else c for c in re.split("([0-9]+)", s)]


# SOURCE: https://github.com/napari/napari/blob/main/napari/plugins/io.py
def magic_imread(filenames, *, use_dask=None, stack=True):
    """
    Dispatch the appropriate reader given some files.

    The files are assumed to all have the same shape.

    Parameters
    ----------
    filenames : list
        List of filenames or directories to be opened.
        A list of `pathlib.Path` objects and a single filename or `Path` object
        are also accepted.
    use_dask : bool
        Whether to use dask to create a lazy array, rather than NumPy.
        Default of None will resolve to True if filenames contains more than
        one image, False otherwise.
    stack : bool
        Whether to stack the images in multiple files into a single array. If
        False, a list of arrays will be returned.

    Returns
    -------
    image : array-like
        Array or list of images

    """
    # cast Path to string
    if isinstance(filenames, Path):
        filenames = filenames.as_posix()

    if len(filenames) == 0:
        return None
    if isinstance(filenames, str):
        filenames = [filenames]  # ensure list

    # replace folders with their contents
    filenames_expanded = []
    for filename in filenames:
        # zarr files are folders, but should be read as 1 file
        if os.path.isdir(filename):
            dir_contents = sorted(
                glob(os.path.join(filename, "*.*")), key=_alphanumeric_key
            )
            # remove subdirectories
            dir_contents_files = filter(lambda f: not os.path.isdir(f), dir_contents)
            filenames_expanded.extend(dir_contents_files)
        else:
            filenames_expanded.append(filename)

    if use_dask is None:
        use_dask = len(filenames_expanded) > 1

    if not filenames_expanded:
        raise ValueError(f"No files found in {filenames} after removing subdirectories")

    # then, read in images
    images = []
    shape = None
    for filename in filenames_expanded:
        if shape is None:
            image = imread(filename)
            shape = image.shape
            dtype = image.dtype
        if use_dask:
            image = da.from_delayed(delayed(imread)(filename), shape=shape, dtype=dtype)
        elif len(images) > 0:  # not read by shape clause
            image = imread(filename)
        images.append(image)
    if len(images) == 1:
        image = images[0]
    elif stack:
        if use_dask:
            image = da.stack(images)
        else:
            try:
                image = np.stack(images)
            except ValueError as e:
                if "input arrays must have the same shape" not in str(e):
                    raise e
                msg = (
                    "To stack multiple files into a single array with "
                    "numpy, all input arrays must have the same shape."
                    " Set `use_dask` to True to stack arrays with "
                    "different shapes."
                )
                raise ValueError(msg) from e
    else:
        image = images  # return a list
    return image


# def guess_zarr_path(path):
#     """Guess whether string path is part of a zarr hierarchy.

#     Parameters
#     ----------
#     path : str
#         Path to a file or directory.

#     Returns
#     -------
#     bool
#         Whether path is for zarr.
#     >>> guess_zarr_path('dataset.zarr')
#     True
#     >>> guess_zarr_path('dataset.zarr/path/to/array')
#     True
#     >>> guess_zarr_path('dataset.zarr/component.png')
#     True
#     """
#     return any(part.endswith(".zarr") for part in Path(path).parts)


# def read_zarr_dataset(path):
#     """Read a zarr dataset, including an array or a group of arrays.

#     Parameters
#     ----------
#     path : str
#         Path to directory ending in '.zarr'. Path can contain either an array
#         or a group of arrays in the case of multiscale data.
#     Returns
#     -------
#     image : array-like
#         Array or list of arrays
#     shape : tuple
#         Shape of array or first array in list
#     """
#     if os.path.exists(os.path.join(path, ".zarray")):
#         # load zarr array
#         image = da.from_zarr(path)
#         shape = image.shape
#     elif os.path.exists(os.path.join(path, ".zgroup")):
#         # else load zarr all arrays inside file, useful for multiscale data
#         image = []
#         for subpath in sorted(os.listdir(path)):
#             if not subpath.startswith("."):
#                 image.append(read_zarr_dataset(os.path.join(path, subpath))[0])
#         shape = image[0].shape
#     else:
#         raise ValueError(f"Not a zarr dataset or group: {path}")
#     return image, shape


def write_csv(
    filename: str,
    data: list | np.ndarray,
    column_names: list[str] | None = None,
):
    """
    Write a csv file.

    Parameters
    ----------
    filename : str
        Filename for saving csv.
    data : list or ndarray
        Table values, contained in a list of lists or an ndarray.
    column_names : list, optional
        List of column names for table data.

    """
    with open(filename, mode="w", newline="") as csvfile:
        writer = csv.writer(
            csvfile,
            delimiter=",",
            quotechar='"',
            quoting=csv.QUOTE_MINIMAL,
        )
        if column_names is not None:
            writer.writerow(column_names)
        for row in data:
            writer.writerow(row)


def guess_layer_type_from_column_names(
    column_names: list[str],
) -> str | None:
    """
    Guess layer type based on column names from a csv file.

    Parameters
    ----------
    column_names : list of str
        List of the column names from the csv.

    Returns
    -------
    str or None
        Layer type if recognized, otherwise None.

    """
    if {"index", "shape-type", "vertex-index", "axis-0", "axis-1"}.issubset(
        column_names
    ):
        return "shapes"
    elif {"axis-0", "axis-1"}.issubset(column_names):
        return "points"
    else:
        return None


def read_csv(
    filename: str, require_type: str = None
) -> tuple[np.array, list[str], str | None]:
    """
    Return CSV data only if column names match format for ``require_type``.

    Reads only the first line of the CSV at first, then optionally raises an
    exception if the column names are not consistent with a known format, as
    determined by the ``require_type`` argument and
    :func:`guess_layer_type_from_column_names`.

    Parameters
    ----------
    filename : str
        Path of file to open
    require_type : str, optional
        The desired layer type. If provided, should be one of the keys in
        ``csv_reader_functions`` or the string "any".  If ``None``, data, will
        not impose any format requirements on the csv, and data will always be
        returned.  If ``any``, csv must be recognized as one of the valid layer
        data formats, otherwise a ``ValueError`` will be raised.  If a specific
        layer type string, then a ``ValueError`` will be raised if the column
        names are not of the predicted format.

    Returns
    -------
    (data, column_names, layer_type) : Tuple[np.array, List[str], str]
        The table data and column names from the CSV file, along with the
        detected layer type (string).

    Raises
    ------
    ValueError
        If the column names do not match the format requested by
        ``require_type``.

    """
    with open(filename, newline="") as csvfile:
        reader = csv.reader(csvfile, delimiter=",")
        column_names = next(reader)

        layer_type = guess_layer_type_from_column_names(column_names)
        if require_type:
            if not layer_type:
                raise ValueError(
                    f'File "{filename}" not recognized as valid Layer data'
                )
            elif layer_type != require_type and require_type.lower() != "any":
                raise ValueError(
                    f'File "{filename}" not recognized as {require_type} data'
                )

        data = np.array(list(reader))
    return data, column_names, layer_type


# def csv_to_layer_data(path: str, require_type: str = None) -> Optional[FullLayerData]:
#     """Return layer data from a CSV file if detected as a valid type.

#     Parameters
#     ----------
#     path : str
#         Path of file to open
#     require_type : str, optional
#         The desired layer type. If provided, should be one of the keys in
#         ``csv_reader_functions`` or the string "any".  If ``None``,
#         unrecognized CSV files will simply return ``None``.  If ``any``,
#         unrecognized CSV files will raise a ``ValueError``.  If a specific
#         layer type string, then a ``ValueError`` will be raised if the column
#         names are not of the predicted format.

#     Returns
#     -------
#     layer_data : tuple, or None
#         3-tuple ``(array, dict, str)`` (points data, metadata, layer_type) if
#         CSV is recognized as a valid type.

#     Raises
#     ------
#     ValueError
#         If ``require_type`` is not ``None``, but the CSV is not detected as a
#         valid data format.
#     """
#     try:
#         # pass at least require "any" here so that we don't bother reading the
#         # full dataset if it's not going to yield valid layer_data.
#         _require = require_type or "any"
#         table, column_names, _type = read_csv(path, require_type=_require)
#     except ValueError:
#         if not require_type:
#             return None
#         raise
#     if _type in csv_reader_functions:
#         return csv_reader_functions[_type](table, column_names)
#     return None  # only reachable if it is a valid layer type without a reader


# def _points_csv_to_layerdata(
#     table: np.ndarray, column_names: List[str]
# ) -> FullLayerData:
#     """Convert table data and column names from a csv file to Points LayerData.

#     Parameters
#     ----------
#     table : np.ndarray
#         CSV data.
#     column_names : list of str
#         The column names of the csv file

#     Returns
#     -------
#     layer_data : tuple
#         3-tuple ``(array, dict, str)`` (points data, metadata, 'points')
#     """

#     data_axes = [cn.startswith("axis-") for cn in column_names]
#     data = np.array(table[:, data_axes]).astype("float")

#     # Add properties to metadata if provided
#     prop_axes = np.logical_not(data_axes)
#     if column_names[0] == "index":
#         prop_axes[0] = False
#     meta = {}
#     if np.any(prop_axes):
#         meta["properties"] = {}
#         for ind in np.nonzero(prop_axes)[0]:
#             values = table[:, ind]
#             try:
#                 values = np.array(values).astype("int")
#             except ValueError:
#                 try:
#                     values = np.array(values).astype("float")
#                 except ValueError:
#                     pass
#             meta["properties"][column_names[ind]] = values

#     return data, meta, "points"


# def _shapes_csv_to_layerdata(
#     table: np.ndarray, column_names: List[str]
# ) -> FullLayerData:
#     """Convert table data and column names from a csv file to Shapes LayerData.

#     Parameters
#     ----------
#     table : np.ndarray
#         CSV data.
#     column_names : list of str
#         The column names of the csv file

#     Returns
#     -------
#     layer_data : tuple
#         3-tuple ``(array, dict, str)`` (points data, metadata, 'shapes')
#     """

#     data_axes = [cn.startswith("axis-") for cn in column_names]
#     raw_data = np.array(table[:, data_axes]).astype("float")

#     inds = np.array(table[:, 0]).astype("int")
#     n_shapes = max(inds) + 1
#     # Determine when shape id changes
#     transitions = list((np.diff(inds)).nonzero()[0] + 1)
#     shape_boundaries = [0] + transitions + [len(table)]
#     if n_shapes != len(shape_boundaries) - 1:
#         raise ValueError("Expected number of shapes not found")

#     data = []
#     shape_type = []
#     for ind_a, ind_b in zip(shape_boundaries[:-1], shape_boundaries[1:]):
#         data.append(raw_data[ind_a:ind_b])
#         shape_type.append(table[ind_a, 1])

#     return data, {"shape_type": shape_type}, "shapes"


# csv_reader_functions = {
#     "points": _points_csv_to_layerdata,
#     "shapes": _shapes_csv_to_layerdata,
# }
