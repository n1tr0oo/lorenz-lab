import jenkins.model.Jenkins
import hudson.security.SecurityRealm
import hudson.plugins.git.GitSCM
import hudson.plugins.git.BranchSpec
import hudson.plugins.git.UserRemoteConfig
import org.jenkinsci.plugins.workflow.job.WorkflowJob
import org.jenkinsci.plugins.workflow.cps.CpsScmFlowDefinition

// This controller is disposable, bound to loopback and contains no credentials.
// A shared or remotely reachable installation must configure authentication
// and use a separate build agent instead of this educational setup.
def instance = Jenkins.get()
instance.setSecurityRealm(SecurityRealm.NO_AUTHENTICATION)
instance.setNumExecutors(1)
def repository = System.getenv('LORENZ_REPOSITORY') ?: 'https://github.com/n1tr0oo/lorenz-lab.git'
def revision = System.getenv('LORENZ_REF') ?: '*/main'
def scm = new GitSCM([new UserRemoteConfig(repository, null, null, null)],
                    [new BranchSpec(revision)], false, [], null, null, [])
def job = instance.getItem('lorenz-lab') ?: instance.createProject(WorkflowJob, 'lorenz-lab')
job.setDescription('Lorenz Lab scientific computation CI and test deployment')
job.setDefinition(new CpsScmFlowDefinition(scm, 'Jenkinsfile'))
job.save()
instance.save()
job.scheduleBuild2(0)
