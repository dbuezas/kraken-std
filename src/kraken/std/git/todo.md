
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
[x] 5. Add a `tokens` parameter to the GitignoreSyncTask constructor (with the standard list as default paramter)
[x]6. Connect Apply task to GitignoreFile ...
[x] fix generation
[x] 7. The apply fn should save a copy of the replaced file .gitignore.old
--- Apply task is ready ---

# Chapter 3 - Check
[x] 1. Create dedicated gitignore_check_task
[x] 2. Make sure __init__/gitignore adds the check task to the check group
[x] 3. call gitignorefile.validate_hash() and return all TaskStatus variations
[x] 3. compare tokens list

# Chapter 4 - Tidy up
[x] const file
[x] revisit \r with other write, read file
[x] parse_file, rename parse
[x] evaluate not inheriting from RenderFileTask
[x] check if RenderFileTask used to do any extra work (like creating a directory, etc)
[x] ensure check task validates gitignore sorting rules
[x] handle the exceptional case of not having an END_GUARD line (it crashes)
[ ] Figure out how to add missing previous entries that aren't covered by gitignore.io
