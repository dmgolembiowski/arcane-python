import abc
import functools
from typing           import ( Union, Callable, Awaitable, Dict, Set )
from inspect          import iscoroutinefunction
from itsdangerous     import TimedJSONWebSignatureSerializer as TJWSS
from itsdangerous.exc import ( SignatureExpired, BadData )

class LinkInterface(metaclass=abc.ABCMeta):
    @classmethod
    def __subclasshook__(cls, sub):
        return ( 
            ((
                hasattr(sub, '__enter__') and callable(sub.__enter__) and
                hasattr(sub, '__exit__') and callable(sub.__exit__)
            ) or
            (
                hasattr(sub, '__aenter__') and callable(sub.__aenter__) and
                hasattr(sub, '__aexit__') and callable(sub.__aexit__)
            )) and
            hasattr(sub, 'generate_uri') and callable(sub.generate_uri) and
            hasattr(sub, 'decode_uri') and callable(sub.decode_uri)
        )

@LinkInterface.register
class AbstractLinkParser:

    def serializer(self, secret_key: str, expires_in: int = -1):
        try:
            assert expires_in < 0
            return TJWSS(secret_key)
        except AssertionError:
            return TJWSS(secret_key, expires_in=expires_in)

    def __enter__(self):
        raise NotImplemented

    def __exit__(self):
        raise NotImplemented

    def generate_uri(
            self,
            data: Dict,
            secret_key : Union[str, None] = None,
            expires_in: int = -1, 
        ) -> str:
        
        return self.serializer(secret_key, expires_in).dumps(data).decode("utf-8")
                
    def decode_uri(
            self,
            uri: Union[str, bytes],
            secret_key: str,
            on_expired: Union[Callable, None] = None,
            on_failure: Union[Callable, None] = None
            ) -> Union[Dict, None]:

        try:
            if type(uri) == str:
                pass
            elif type(uri) == bytes:
                uri = uri.decode("utf-8")
            else:
                raise ValueError
            loaded = self.serializer(secret_key).loads(uri)
        except SignatureExpired:
            loaded = {"error": "Link has expired."}
        except BadData:
            loaded = {"error": "Link is invalid." }
        finally:
            return loaded

class RegistryInterface(metaclass=abc.ABCMeta):
    @classmethod
    def __subclasshook__(cls, sub):
        return (
        (( 
            hasattr(sub, 'create') and callable(sub.create) 
        ) or
        (
            hasattr(sub, 'async_create') and callable(sub.async_create)
        )) and
        ((
            hasattr(sub, 'delete') and callable(sub.delete)
        ) or
        (
             hasattr(sub, 'async_delete') and callable(sub.async_delete)   
        )) and
        (
            hasattr(sub, '__keystore__') 
        ) and
        (
            hasattr(sub, '__setitem__') and callable(sub.__setitem__)
        ) and
        (
            hasattr(sub, '__getitem__') and callable(sub.__getitem__)
        ) and
        ((
            hasattr(sub, 'retrieve') and callable(sub.retrieve)
        ) or
        (
            hasattr(sub, 'async_retrieve') and callable(sub.async_retrieve)
        )))

class ActionInterface(metaclass=abc.ABCMeta):
    @classmethod
    def __subclasshook__(cls, sub):
        return (
        # Synchronous, blocking code behavior
        ((
            hasattr(sub, '__behavior__')
        ) and
        # Without context management
        ((
            hasattr(sub, '__call__') and callable(sub.__call__)
        ) or 
        # With context management
        ((
            hasattr(sub, '__call__') and callable(sub.__call__)
        ) and
        (
            hasattr(sub, '__enter__') and callable(sub.__enter__)
        ) and
        (
            hasattr(sub, '__exit__') and callable(sub.__exit__)
        ))))
        or
        # Asynchronous, non-blocking code behavior
        ((
            hasattr(sub, '__async_behavior__')
        ) and
        # Without asynchronous context management
        ((
            hasattr(sub, '__await__') and callable(sub.__await__)
        ) or
        # With asynchronous context management
        ((
            hasattr(sub, '__await__') and callable(sub.__await__)
        ) and
        (
            hasattr(sub, '__aenter__') and callable(sub.__aenter__)
        ) and
        (
            hasattr(sub, '__aexit__') and callable(sub.__aexit__)
        ))
        )))

@ActionInterface.register
class AbstractAction:
    def __init__(self, func: Union[Callable, None] = None , **kwargs):
        self._behavior_store = lambda: NotImplemented
        self.__behavior__ = func
        self.__dict__.update(kwargs)

    def __call__(self, *args, **kwargs):
        return self.__behavior__(*args, **kwargs)

    @property
    def __behavior__(self) -> Union[Callable]:
        return self._behavior_store

    @__behavior__.setter
    def __behavior__(self, func, *args, **kwargs) -> None:
        if func is not None and not iscoroutinefunction(func):
            self._behavior_store = self.__class__._gen_wrapper(func, *args, **kwargs)
        else:
            raise ValueError("""
            Illegal target type 'coroutine' assigned.
            Consider replacing the `func` parameter with
            a blocking, synchronous function instead of a 
            coroutine function. Otherwise, use a class that 
            inherits from the `AbstractAsyncAction` type.""")

    @staticmethod
    def _gen_wrapper(
            Func,
            *Partial_Args,
            **Partial_Kwargs) -> Callable:
        @functools.wraps(Func)
        def _generic(*args, **kwargs):
            return Func(
                *args, *Partial_Args,
                **kwargs, **Partial_Kwargs
            )
        return _generic

@ActionInterface.register
class AbstractAsyncAction:

    def __init__(self, coro: Union[Awaitable, None] = None , **kwargs):
        async def default():
            return NotImplemented
        self._behavior_store = default
        self.__async_behavior__ = coro
        self.__dict__.update(kwargs)

    def __await__(self, *args, **kwargs):
        return self.__async_behavior__(*args, **kwargs).__await__()

    @property
    def __async_behavior__(self) -> Union[Callable]:
        return self._behavior_store

    @__async_behavior__.setter
    def __async_behavior__(self, coro, *args, **kwargs) -> None:
        if coro is not None and iscoroutinefunction(coro):
            self._behavior_store = self.__class__._gen_wrapper(coro, *args, **kwargs)
        else:
            raise ValueError("""
            Illegal non-coroutine target type assigned.
            Please supply an async function to the `coro`
            paramter or replace this action with a blocking,
            synchronous class instance that inherits from the
            `AbstractAction` type.""")

    @staticmethod
    def _gen_wrapper(
            Func,
            *Partial_Args,
            **Partial_Kwargs) -> Callable:
        @functools.wraps(Func)
        def _generic(*args, **kwargs):
            return Func(
                *args, *Partial_Args,
                **kwargs, **Partial_Kwargs
            )
        return _generic   


class DownloadInterface:
    @property
    def __behavior__(self):
        return lambda : None

    @__behavior__.setter
    def __behavior__(self, behavior_function):
        pass

    @classmethod
    def __subclasshook__(cls, sub):
        return (
            (
                (
                    hasattr(sub, '__aenter__') and hasattr(sub, '__aexit__') and
                    callable(sub.__aenter__) and callable(sub.__aexit__)
                )
                or
                (
                    hasattr(sub, '__enter__') and hasattr(sub, '__exit__') and
                    callable(sub.__enter__) and callable(sub.__exit__)
                )
            ) and 
            (
                hasattr(sub, 'before_download') and callable(sub.before_download) or
                NotImplemented
            ) and
            (
                hasattr(sub, 'after_download') and callable(sub.after_download) or
                NotImplemented
            ) or NotImplemented
        )

class UploadInterface(metaclass=abc.ABCMeta):
    @classmethod
    def __subclasshook__(cls, sub):
        return (
            (
                (
                    hasattr(sub, '__aenter__') and hasattr(sub, '__aexit__') and
                    callable(sub.__aenter__) and callable(sub.__aexit__)
                )
                or
                (
                    hasattr(sub, '__enter__') and hasattr(sub, '__exit__') and
                    callable(sub.__enter__) and callable(sub.__exit__)
                )
            ) and 
            (
                hasattr(sub, 'before_upload') and callable(sub.before_upload) or
                NotImplemented
            ) and
            (
                hasattr(sub, 'after_upload') and callable(sub.after_upload) or
                NotImplemented
            ) or NotImplemented
        )

__all__ = (
        'AbstractAction',
        'AbstractAsyncAction',
        'AbstractLinkParser',
        'ActionInterface',
        'DownloadInterface',
        'LinkInterface',
        'RegistryInterface',
        'UploadInterface'
        )
