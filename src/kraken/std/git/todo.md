
Action plan
# Chapter 1 - Cleanup
1. Remove all deprecated functionality (add_paths, etc)
2. Find out how other singleton tasks handle not being added multiple times
3. Remove task.create_check() and replace it with gitignore_check_task

--- we have two tasks that don't do anything ---
# Chapter 2 - Apply

1. GitignoreFile class, add
    - generated_content instance property
    - generated_content_token_list
    - generated_content_hash 
    - refresh_gen_content: fn that receives tokens and fetches gitignore files from gitignore.io and stores them inside an instance variable
    - refresh_gen_content_hash:
        - everything between the guards is hashed including the token list
    - fn to validate the hash 
        - also compare the token list.
    - Extend parser to cover
        - generated_content
        - generated_content_token_list
        - generated_content_hash 
5. Add a `tokens` parameter to the GitignoreSyncTask constructor (with the standard list as default paramter)
6. Connect Apply task to GitignoreFile ...
7. The apply fn should save a copy of the replaced file .gitignore.old
--- Apply task is ready ---

# Chapter 3 - Check
1. Create dedicated gitignore_check_task
2. Make sure __init__/gitignore adds the check task to the check group
3. call gitignorefile.validate_hash() and return all TaskStatus variations
3. compare tokens list

