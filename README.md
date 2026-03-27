# cobots

This repository contains my AI tooling setup; all my agent files, instruction files, and skills.
Most of these, I've written myself (some with the help of AI).
Others, I've copied and modified to my liking (I've added notes to each of these).
This is primarily intended to be used with GitHub Copilot or other AI-assisted coding agent tools.

The name **cobots** comes from one (or all) of these:

* *Connor's Bots*
* *Coding Bots*
* *Collaborating Bots*
* *Cool Binary Output Technicians*
* *Coordinated Operating Bots*
* *Confusing, overthought, binary-optimizing totality*
* ...alright I'm out of ideas

## The System

So far, the system of agents works like this:

* [The Director](agents/director.cobots.agent.md) understands the goals of a project/problem and comes up with a high-level plan of what tasks are involved, and what other agents should complete them.
* [The Architect](agents/architect.cobots.agent.md) creates a comprehensive design report on how a software system should be design (or how a problem should be solved).
* [The Developer](agents/developer.cobots.agent.md) implements the architect's design.
* [The Scrutinizer](agents/scrutinizer.cobots.agent.md) reviews the implementation (or anything else requested) and suggests improvements to be made.
* [The Documenter](agents/documenter.cobots.agent.md) writes documentation for the project.

The following skills are used by the agents to track work and report progress:

* [Cobots Tasks CLI](skills/cobots_tasks/) - A small CLI tool that creates and manages `*.task.md` files under a working directory.
    * Tasks represent individual items that need completing for the project.
* [Cobots Reports CLI](skills/cobots_reports/) - A small CLI tool that creates `*.report.md` files under a working directory.
    * Reports represent write-ups created by the agents, such as architecture plans, code reviews, etc.

## Resources

A few useful resources that I've learned from:

* [Awesome GitHub Copilot](https://awesome-copilot.github.com/) - A collection of agents, skills, instructions, etc.
* [How to write a great `agents.md`](https://github.blog/ai-and-ml/github-copilot/how-to-write-a-great-agents-md-lessons-from-over-2500-repositories/)

