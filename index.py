import json
import boto3
import logging
#setup simple logging for INFO
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    ec2_client = boto3.client('ec2')
    CW_client = boto3.client('cloudwatch')
    regions = ['eu-west-1']
    fun_name = context.function_name
    env = fun_name.split('-')
    env_name = env[2].upper()
    #print('check here', env_name)
    full_env_name = "ADOP-E-" + env_name + "-CJE"
    print('nishant check here', full_env_name)
    
    if env_name == "UAT":
        client = ['build', 'master']
    else:
        client = ['build', 'master', 'msdo', 'aicpa-rave']
        
    for region in regions:
        new_widgets = []
        EXISTING_DASHBOARD = []
        #pre_cw_dashboard = CW_client.get_dashboard(DashboardName='mywizard-dmt-uat-jenkins-cw-dashboard')
        pre_cw_dashboard = CW_client.get_dashboard(DashboardName="mywizard-dmt-" + env[2] + "-jenkins-cw-dashboard")
        print ('nishant', pre_cw_dashboard)
        data = json.loads(pre_cw_dashboard['DashboardBody'])
        #print(data['widgets'])
        for item in data['widgets']:
            value = item['properties'].get('title', None)
            print("check", value)
            #if value == "buildWorkers_CPU" or value == "buildWorkers_FREEMEM" or value == "buildWorkers_USEDMEM" or value == "masterWorkers_CPU" or value == "masterWorkers_FREEMEM" or value == "masterWorkers_USEDMEM":
            if value == "buildWorkers_CPU" or value == "buildWorkers_FREEMEM" or value == "buildWorkers_USEDMEM" or value == "masterWorkers_CPU" or value == "masterWorkers_FREEMEM" or value == "masterWorkers_USEDMEM" or value == "msdoWorkers_CPU" or value == "msdoWorkers_FREEMEM" or value == "msdoWorkers_USEDMEM" or value == "aicpa-raveWorkers_CPU" or value == "aicpa-raveWorkers_FREEMEM" or value == "aicpa-raveWorkers_USEDMEM":
                print("Don't copy it.", value)
            else:
                EXISTING_DASHBOARD.append(json.dumps(item))
        NewDashboard = ','.join([str(elem) for elem in EXISTING_DASHBOARD])
        #for params in ['build', 'master']:
        for params in client:
            ec2 = boto3.resource('ec2', region_name=region)
            instances = ec2.instances.filter(
                Filters = [
                    
                    {'Name': 'instance-state-name', 'Values': ['running', 'pending']},
                    {'Name': 'tag:alpha.eksctl.io/cluster-name', 'Values': [f'{full_env_name}']},
                    {'Name': 'tag:k8s.io/cluster-autoscaler/node-template/label/worker', 'Values': [params]}
                ]
                
            )
            
            CPUUtilization_template = '["AWS/EC2", "CPUUtilization", "InstanceId", "{}"]'
            memfree_template = '["CWAgent", "mem_free", "InstanceId", "{}"]'
            memactive_template = '["CWAgent", "mem_active", "InstanceId", "{}"]'
            
            CPUUtilization_array = []
            memfree_array = []
            memactive_array = []



            for i in instances.all():
                print(i.id, params)
                instance_id = i.id

                CPUUtilization_array.append(CPUUtilization_template.format(i.id))
                memfree_array.append(memfree_template.format(i.id))
                memactive_array.append(memactive_template.format(i.id))
                
                
            CPUUtilization_string = ",".join(CPUUtilization_array)
            memfree_string = ",".join(memfree_array)
            memactive_string = ",".join(memactive_array)

            
            
            CPUUtilization_instances = r'{"type": "metric", "x": 0, "y": 0, "width": 24, "height": 6, "properties": {"metrics": [template], "view": "timeSeries", "stacked": false, "region": "eu-west-1", "stat": "Average", "period": 300, "title": "params"}}'.replace("template", CPUUtilization_string).replace("params", params +'Workers_CPU')
            memfree_instances = '{"type": "metric", "x": 0, "y": 0, "width": 24, "height": 6, "properties": {"metrics": ['+memfree_string+r'], "view": "timeSeries", "stacked": false, "region": "eu-west-1", "stat": "Average", "period": 300, "title": "params"}}'.replace("params", params +'Workers_FREEMEM')
            memactive_instances = '{"type": "metric", "x": 0, "y": 0, "width": 24, "height": 6, "properties": {"metrics": ['+memactive_string+r'], "view": "timeSeries", "stacked": false, "region": "eu-west-1", "stat": "Average", "period": 300, "title": "params"}}'.replace("params", params +'Workers_USEDMEM')
            new_widgets.append(CPUUtilization_instances)
            new_widgets.append(memfree_instances)
            new_widgets.append(memactive_instances)            
            

        DashboardBody='{"widgets":[' + NewDashboard + ', ' + ','.join([str(elem) for elem in new_widgets]) + ']}'
        print(DashboardBody)
        response = CW_client.put_dashboard(DashboardName="mywizard-dmt-" + env[2] + "-jenkins-cw-dashboard", DashboardBody=DashboardBody)
