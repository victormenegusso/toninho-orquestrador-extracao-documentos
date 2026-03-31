# Piloting GitHub Copilot coding agent in your organization

Follow best practices to enable Copilot coding agent in your organization.

<!--JTBD: When rolling out Copilot coding agent, I want to understand use cases and follow best practices, so I can ensure I'm using it as intended and get value from a pilot program.-->

Copilot coding agent is an autonomous, AI-powered agent that completes software development tasks on GitHub. Adopting Copilot coding agent in your organization frees your engineering teams to spend more time thinking strategically and less time making routine fixes and maintenance updates in a codebase.

Copilot coding agent:

* **Joins your team**: Developers can delegate work to Copilot unlike IDE-based coding agents that require synchronous pairing sessions. Copilot opens draft pull requests for team members to review and iterates based on feedback, as a developer would.
* **Reduces context switching**: Developers working in JetBrains IDEs, VS Code, Visual Studio, or GitHub.com can ask Copilot coding agent to create a pull request to complete small tasks without stopping what they are currently doing.
* **Executes tasks in parallel**: Copilot can work on multiple issues simultaneously, handling tasks in the background while your team focuses on other priorities.

## 1. Evaluate

Before enabling Copilot coding agent for members, understand how Copilot coding agent will fit into your organization. This will help you evaluate whether Copilot coding agent is suitable for your needs and plan communications and training sessions for developers.

1. Learn about Copilot coding agent, including the costs, built-in security features, and how it differs from other AI tools your developers may be used to. See [About GitHub Copilot coding agent](/en/enterprise-cloud@latest/copilot/concepts/about-copilot-coding-agent).
2. Learn about the tasks that Copilot coding agent is best suited for. These are generally well-defined and scoped issues, such as increasing test coverage, fixing bugs or flaky tests, or updating config files or documentation. See [Best practices for using GitHub Copilot to work on tasks](/en/enterprise-cloud@latest/copilot/tutorials/coding-agent/best-practices).
3. Consider how Copilot coding agent fits alongside other tools in your organization's workflows. For an example scenario that walks through how to use Copilot coding agent alongside other AI features on GitHub, see [Integrating agentic AI into your enterprise's software development lifecycle](/en/enterprise-cloud@latest/copilot/rolling-out-github-copilot-at-scale/enabling-developers/integrating-agentic-ai).

## 2. Secure

All AI models are trained to meet a request, even if they don't have all the information needed to provide a good answer, and this can lead them to make mistakes. By following best practices, you can build on the default security features of Copilot coding agent.

1. Give Copilot the information it needs to work successfully in a repository using a `copilot-instructions.md` file. See [Adding repository custom instructions for GitHub Copilot](/en/enterprise-cloud@latest/copilot/customizing-copilot/adding-repository-custom-instructions-for-github-copilot).
2. Set up the Copilot development environment for a repository with access to the tools and package repositories approved by the organization using a `copilot-setup-steps.yml` file and local MCP servers. See [Customizing the development environment for GitHub Copilot coding agent](/en/enterprise-cloud@latest/copilot/customizing-copilot/customizing-the-development-environment-for-copilot-coding-agent) and [Extending GitHub Copilot coding agent with the Model Context Protocol (MCP)](/en/enterprise-cloud@latest/copilot/using-github-copilot/coding-agent/extending-copilot-coding-agent-with-mcp).
3. Follow best practices for storing secrets securely. See [Using secrets in GitHub Actions](/en/enterprise-cloud@latest/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions).
4. Enable code security features to further lower the risk of leaking secrets and introducing vulnerabilities into the code. See [Creating a custom security configuration](/en/enterprise-cloud@latest/code-security/securing-your-organization/enabling-security-features-in-your-organization/creating-a-custom-security-configuration).
5. Configure your branch rulesets to ensure that all pull requests raised by Copilot are approved by a second user with write permissions (a sub-option of "Require a pull request before merging"). See [Enforcing code governance in your enterprise with rulesets](/en/enterprise-cloud@latest/admin/enforcing-policies/enforcing-policies-for-your-enterprise/enforcing-policies-for-code-governance), [Creating rulesets for repositories in your organization](/en/enterprise-cloud@latest/organizations/managing-organization-settings/creating-rulesets-for-repositories-in-your-organization) and [Available rules for rulesets](/en/enterprise-cloud@latest/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets#require-a-pull-request-before-merging).

## 3. Pilot

<a href="https://github.com/github-copilot/purchase?ref_product=copilot&ref_type=trial&ref_style=button&ref_plan=enterprise" target="_blank" class="btn btn-primary mt-3 mr-3 no-underline"><span>Sign up for Copilot</span> <svg version="1.1" width="16" height="16" viewBox="0 0 16 16" class="octicon octicon-link-external" aria-label="link external icon" role="img"><path d="M3.75 2h3.5a.75.75 0 0 1 0 1.5h-3.5a.25.25 0 0 0-.25.25v8.5c0 .138.112.25.25.25h8.5a.25.25 0 0 0 .25-.25v-3.5a.75.75 0 0 1 1.5 0v3.5A1.75 1.75 0 0 1 12.25 14h-8.5A1.75 1.75 0 0 1 2 12.25v-8.5C2 2.784 2.784 2 3.75 2Zm6.854-1h4.146a.25.25 0 0 1 .25.25v4.146a.25.25 0 0 1-.427.177L13.03 4.03 9.28 7.78a.751.751 0 0 1-1.042-.018.751.751 0 0 1-.018-1.042l3.75-3.75-1.543-1.543A.25.25 0 0 1 10.604 1Z"></path></svg></a>

> \[!TIP] You need GitHub Copilot Pro, GitHub Copilot Pro+, GitHub Copilot Business or GitHub Copilot Enterprise to use Copilot coding agent.

As with any other change to working practices, it's important to run a trial to learn how to deploy Copilot coding agent effectively in your organization or enterprise.

1. Gather a cross-functional team for the trial to bring different roles, backgrounds, and perspectives to the project. This will make it easier to ensure that you explore a broad range of ways to define issues, assign work to Copilot, and give clear review feedback.
2. Choose an isolated or low-risk repository, for example, one that contains documentation or internal tools. You could create a fresh repository to use as a playground, but Copilot needs context to be successful, so you would need to add a lot of context, including team processes, development environment, and common dependencies.
3. Enable Copilot coding agent in the repository and optionally enable third-party MCP servers for enhanced context sharing. See [Adding GitHub Copilot coding agent to your organization](/en/enterprise-cloud@latest/copilot/managing-copilot/managing-github-copilot-in-your-organization/adding-copilot-coding-agent-to-organization).
4. Create repository instructions and pre-install any tools required in the development environment Copilot uses. See [Customizing the development environment for GitHub Copilot coding agent](/en/enterprise-cloud@latest/copilot/customizing-copilot/customizing-the-development-environment-for-copilot-coding-agent).
5. Identify a few compelling use cases for your organization, for example: test coverage or improving accessibility. See [Choose the right type of tasks to give to Copilot](/en/enterprise-cloud@latest/copilot/tutorials/coding-agent/best-practices#choosing-the-right-type-of-tasks-to-give-to-copilot) in the best practice guide.
6. Use best practice to create or refine issues for Copilot in your pilot repository.
7. Assign issues to Copilot and prepare team members to review its work.
8. Spend time looking at the codebase or documentation in VS Code or GitHub.com, asking Copilot to create a pull request to fix any bugs or small improvements that you identify.

Over the course of the trial, the team should iterate on the repository instructions, installed tools, access to MCP servers, and issue definition to identify how your organization can get the most from Copilot coding agent. This process will help you identify your organization's best practices for working with Copilot and plan an effective rollout strategy.

In addition to giving you insight into how to set up Copilot coding agent for success, you'll learn how Copilot uses premium requests and actions minutes. This will be valuable when you come to set and manage your budget for a broader trial or full rollout. See [Managing your company's spending on GitHub Copilot](/en/enterprise-cloud@latest/copilot/rolling-out-github-copilot-at-scale/assigning-licenses/managing-your-companys-spending-on-github-copilot).

### Enhancing with MCP

The Model Context Protocol (MCP) is an open standard that defines how applications share context with large language models (LLMs). MCP provides a standardized way to provide Copilot coding agent with access to different data sources and tools.

Copilot coding agent has access to the full GitHub context of the repository it's working in, including issues and pull requests, using the built-in GitHub MCP server. By default, it's restricted from accessing external data by authentication barriers and a firewall.

You can extend the information available to Copilot coding agent by giving it access to local MCP servers for the tools your organization uses. For example, you might want to provide access to local MCP servers for some of the following contexts:

* **Project planning tools**: Allow Copilot direct access to private planning documents that are stored outside GitHub in tools like Notion or Figma.
* **Augment training data**: Each LLM contains training data up to a specific cut-off date. If you're working with fast moving tools, Copilot may not have access to information on new features. You can fill this knowledge gap by making the tool's MCP server available. For example, adding the Terraform MCP server will give Copilot access to the most recently supported Terraform providers.

For more information, see [Extending GitHub Copilot coding agent with the Model Context Protocol (MCP)](/en/enterprise-cloud@latest/copilot/using-github-copilot/coding-agent/extending-copilot-coding-agent-with-mcp).

## Next steps

When you're satisfied with the pilot, you can:

* Enable Copilot coding agent in more organizations or repositories.
* Identify more use cases for Copilot coding agent and train developers accordingly.
* Continue to collect feedback and measure results.

To assess the impact of a new tool, we recommend measuring the tool's impact on your organization's downstream goals. For a systematic approach to driving and measuring improvements in engineering systems, see GitHub's [Engineering System Success Playbook](https://resources.github.com/engineering-system-success-playbook/).
