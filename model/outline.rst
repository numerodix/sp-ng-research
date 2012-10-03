QueuedUrl
-----
- id : any
- url : string
- level : int
- type : anchor|img|script|iframe|...

Url
-----
- id : int/hash
- url : string
- level : int
- status : int
- visited : datetime
- children : [Url]

Web
-----
- root : Url
