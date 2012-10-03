QueuedUrl
-----
- id : any
- url : string
- level : int
- type : anchor|img|script|iframe|...

Queue
-----
- urls: [Url]

Url
-----
- id : int/hash
- url : string
- level : int
- type : anchor|img|script|iframe|...

- status : int
- visited : datetime
- parent: Url
- children : [Url]

Web
-----
- root : Url
