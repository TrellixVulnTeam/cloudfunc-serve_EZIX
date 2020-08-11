# coding=utf-8

from flask import abort, Response
import requests
from guniflask.web import blueprint, put_route, post_route
from guniflask.service_discovery import LoadBalancedRequest, LoadBalancerClient

from cloudfunc_serve.services.docker import DockerService


@blueprint
class CloudFuncController:
    def __init__(self, docker_service: DockerService, load_balanced_request: LoadBalancedRequest,
                 load_balancer_client: LoadBalancerClient):
        self.docker_service = docker_service
        self.load_balanced_request = load_balanced_request
        self.load_balancer_client = load_balancer_client

    @put_route('/cloud-funcs/restart')
    def restart_cloud_func(self, name: str):
        self.docker_service.restart_could_func(name=name)
        return 'success'

    @post_route('/cloud-funcs/run')
    def run_cloud_func(self, name: str):
        if '.' not in name:
            abort(400, 'cloud function name format: <package_name>.<function_name>')
        project_name, func_name = name.split('.', maxsplit=1)
        try:
            resp = self.load_balanced_request.post(f'http://{project_name}/cloud-funcs/{func_name}')
        except Exception as e:
            abort(500, str(e))
        else:
            try:
                resp.raise_for_status()
            except requests.HTTPError:
                abort(500, resp.content)
            return Response(response=resp.content, content_type='application/octet-stream')
