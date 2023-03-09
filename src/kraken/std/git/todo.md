
Action plan
# Chapter 1 - Cleanup
[x] 1. Remove all deprecated functionality (add_paths, etc)
[x] 2. Find out how other singleton tasks handle not being added multiple times
[x] 3. Remove task.create_check() and replace it with gitignore_check_task

--- we have two tasks that don't do anything ---
# Chapter 2 - Apply

[x]1. GitignoreFile class, add
[x] - generated_content instance property
[x] - generated_content_token_list
[x] - generated_content_hash 
[x]    - refresh_gen_content: fn that receives tokens and fetches gitignore files from gitignore.io and stores them inside an instance variable
[x]  - refresh_gen_content_hash: - everything between the guards is hashed including the token list
[x]  - fn to validate the hash 
[x]     - also compare the token list.
[x]    - Extend parser to cover
[x]        - generated_content
[x]        - generated_content_token_list
[x]        - generated_content_hash 
~5. Add a `tokens` parameter to the GitignoreSyncTask constructor (with the standard list as default paramter)~
[x]6. Connect Apply task to GitignoreFile ...
[ ] fix generation
[x] 7. The apply fn should save a copy of the replaced file .gitignore.old
--- Apply task is ready ---

# Chapter 3 - Check
1. Create dedicated gitignore_check_task
2. Make sure __init__/gitignore adds the check task to the check group
3. call gitignorefile.validate_hash() and return all TaskStatus variations
3. compare tokens list

# Chapter 4 - Tidy up
[x] const file
[] revisit \r with other write, read file
[x] parse_file, rename parse
[] evaluate not inheriting from RenderFileTask

