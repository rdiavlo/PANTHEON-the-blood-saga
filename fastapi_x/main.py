"""
# why add type hints?
1. use auto-completion and get error checks in the bargain
2. use static type checking lib


Simple types¶
    You can declare all the standard Python types, not only str.

    You can use, for example:
    int
    float
    bool
    bytes

Generic types with type parameters¶
    There are some data structures that can contain other values, like dict, list, set and tuple. And the internal values can have their own type too.

    These types that have internal types are called "generic" types. And it's possible to declare them, even with their internal types.

    To declare those types and the internal types, you can use the standard Python module typing. It exists specifically to support these type hints.

Newer versions of Python: As Python advances, newer versions come with improved support for these type annotations and in many cases you won't even need to import and use the typing module to declare the type annotations.

"""
# adding type hints
from typing import Optional, Annotated
from enum import Enum
from fastapi import FastAPI, Query
from pydantic import BaseModel, AfterValidator


class Emperor:
    emperor_name = 1

class ModelName(str, Enum):
    goggins = "hoohah"
    napolean = "aaa... kawaii senpai, aa. aaRIGATOOO"
    alexander = "if he dies he dies"



# test type hinting
def say_something_cool(something_cool: str | Emperor) -> Emperor:
    print("saying something cool")
    print(something_cool)
    return Emperor()


say_something_cool(Emperor())


app = FastAPI()


# path parameters
@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}

@app.get("/models/{model_name}")
async def get_model(model_name: ModelName):
    if model_name == ModelName.goggins:
        return {"message": model_name.goggins}
    elif model_name == ModelName.napolean:
        return {"message": model_name.napolean}
    elif model_name == ModelName.alexander:

        return {"message": model_name.alexander}

# query parameters
@app.get("/products/{item_id}")
async def read_item(item_id: int, show_something_cool: bool = False, some_cool_text: str | None = None):
    if show_something_cool:
        if some_cool_text is None:
            some_cool_text = "On your feet soldier!!!"
        return {"item_id": str(item_id) + " " +  some_cool_text}
    return {"item_id": str(item_id)}


# send a request body
class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None

@app.post("/items/")
async def create_item(item: Item):
    return f"data on item {item.name} sent"


# query validation - string. with custom validation
def check_valid_id(id_list: list[str]):
    for id in id_list:
        if not id.startswith(("isbn-", "imdb-")):
            raise ValueError('Invalid ID format, it must start with "isbn-" or "imdb-"')
    return id_list


@app.get("/items/")
async def read_items(q: Annotated[list[str] | None, Query(
    title="Query string",
    description="Query string for the items to search in the database that have a good match",
    max_length=50
    ), AfterValidator(check_valid_id) ] = None):
    results = {"items": [{"item_id": "Foo"}, {"item_id": "Bar"}]}
    if q:
        results.update({"q": q})
    return results