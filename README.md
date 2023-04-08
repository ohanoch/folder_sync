Possible improvements:
- After running the code it will always have "file_record" empty in the first loop. This means that for files that are identical in source and replica it will not know that they were already copied over and will attempt to do it anyways, causing it to md5 them and then perform a "move" action for the file in the replica to the same place it already is at.
	- This can be fixed by logging the file_record in an external file and loading it back in when starting the code. It requires using json, or other formats.

- I was running into problems when quiting the program while the loop is sleeping. Ideally a interupt signal can be sent to the original thread to kill it. Need to figure that out still
