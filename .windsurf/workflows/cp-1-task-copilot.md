---
description: Task copilor
auto_execution_mode: 3
---

We aim to create small, self-contained task which can be easily implemented without understanding the system.
When writing an issue - think "Could a competent junior engineer implement this correctly from only the task definition, relevant file, and tests — without a tour of the whole repo?" 

1. Review feature file, contents of docs/architecture/*, identify relevant rules applicable to this issue. Explicitly state goal, rules, principal architecture patterns, important implementation details. Remind that tests have to be runnable be pytest.

2. Create an issue:
Main principle: its like you are giving the class to the junior developer to implement - you don't trust junior developer to get everything right. Your task definition shall contain skeleton(s) for all files/classes - all methods, properties, fields; with docstrings with return types with examples and parameter examples.

a) Form a checklist-style task list following .windsurf/rules/do-github-issues.md gudance
b) This task list has to include steps "update task checkboxes in the issue for done items" after each major block
c) and commits "feat(name): add small_increment" after each major block
d) provide a set of test cases that cover all scenarios you want the piece to satisfy
e) explicitly state that copilot has to follow red-green-refactor cycle

3. If you see that we are going into complex task (more than 3-5 classes total and/or 18-20 methods total - stop and advise user that we need to split story so Copilot has a chance to implement it.
Propose how you want to split into issue into subissues:
a) create a "parent story" for the entire scenario
b) design contract: skeleton of the class/interface/APIs/services etc. that will be used by other components - linked stories will be implementing different parts of the defined contract + tests to prove implementation correct
c) add linked stories under it (use "Related to:") - to implement util method(s) and its tests (example: "methods take any string with suspected date and returns datetime"), main success scenario (example: "clicks ASSIGN and its linked to the user"), extensions to the main scenario (example: "or clicks FIND button - then lookup dialog opens where user can pick and assign one of his team mates"), ane extra services (example: "maps Tasks oData fields to the Objective fields")
d) in issue description explain branch strategy:
* create a new branch for the entire EPIC (eg features/epic_name)
* create a new branch for each linked story (eg features/epic_name/story_name)
* merge linked stories into the epic branch (eg features/epic_name/story_name -> features/epic_name)
* merge epic after user acceptance into main branch (eg features/epic_name -> main)

4. Accept user guidance - go with your proposal, modify it, or go single story.

5. Add explicit checkboxes to 
a) verify against every section (one section - one checkbox) of .windsurf/workflows/dev-5-check-dod.md contents 
b) checkboxes to update progress instructions so we clearly see checks performed/skipped
c) stress that all tests has to be green
d) add exit criteria - if any of the checkboxes are not checked continue

6. Add explicit checkboxes to verify against .windsurf/workflows/dev-6-finalize-feature.md contents + update progress instructions so we clearly see checks performed

7. Add task for copilot to think about what is amiss in issue and task definition making its job harder. Request adding a comment to the PR calling out @user and presenting recommendations: "To make issue implementation faster and better next time, it would help if you @user will provide: ... "

8. Present issue content to the user for review and approval, do not create yet. Incorporate changes if any.

9. Make sure that all branches/files necessary for the implementation are checked in, committed and pushed to the remote repository.

10. Assign issue to copilot. If there are multiple linked issues - tell copilot which tasks to start with and how to proceed, one by one.