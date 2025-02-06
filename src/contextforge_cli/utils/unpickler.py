"""unpickler.py"""

# Safe unpickler to prevent arbitrary code execution
from __future__ import annotations

import pickle
from types import SimpleNamespace
from typing import Any

safe_list = {
    ("collections", "OrderedDict"),
    ("torch._utils", "_rebuild_tensor_v2"),
    ("torch", "FloatStorage"),
}


class RestrictedUnpickler(pickle.Unpickler):
    """
    _summary_

    Args:
    ----
        pickle (_type_): _description_

    """

    def find_class(self, module: Any, name: Any) -> Any:
        """
        _summary_

        Args:
        ----
            module (_type_): _description_
            name (_type_): _description_

        Raises:
        ------
            pickle.UnpicklingError: _description_

        Returns:
        -------
            _type_: _description_

        """
        # Only allow required classes to load state dict
        if (module, name) not in safe_list:
            raise pickle.UnpicklingError(f"Global '{module}.{name}' is forbidden")
        return super().find_class(module, name)


RestrictedUnpickle = SimpleNamespace(
    Unpickler=RestrictedUnpickler,
    __name__="pickle",
    load=lambda *args, **kwargs: RestrictedUnpickler(*args, **kwargs).load(),
)
