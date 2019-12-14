import logging
import requests
import dateutil.parser
from auth0.v3.authentication import GetToken

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

logger = logging.getLogger(__name__)


class MeshApiException(Exception):
    """Base class for exceptions in this module"""
    pass


class NYCMeshApi(object):

    def __init__(self, domain=None, client_id=None, client_secret=None):

        self.domain = domain if domain else settings.AUTH0_DOMAIN
        self.client_id = client_id if client_id else settings.AUTH0_CLIENT_ID
        self.client_secret = client_secret if client_secret else settings.AUTH0_CLIENT_SECRET
        self.audience = "https://api.nycmesh.net"

        self.token = None
        self.headers = None

        self._setupToken()

    def _setupToken(self):
        get_token = GetToken(self.domain)
        token = get_token.client_credentials(self.client_id, self.client_secret, self.audience)

        self.token = token['access_token']
        self.headers = {'Authorization': 'Bearer ' + self.token}

    def getRequests(self):
        try:
            data = self._get("/v1/requests")
            if "error" in data:
                if "Not found" in data['error']:
                    raise ObjectDoesNotExist()
                else:
                    raise MeshApiException(data['error'])
        except requests.exceptions.RequestException:
            logger.exception("NYCMesh API Request Failed")
            raise
        except Exception:
            logger.exception("NYCMesh API Request Failed")

        return data

    def getRequest(self, request_id):
        try:
            data = self._get(f"/v1/requests/{request_id}")
            if "error" in data:
                if "Not found" in data['error']:
                    raise ObjectDoesNotExist()
                else:
                    raise MeshApiException(data['error'])
        except requests.exceptions.RequestException:
            logger.exception(f"NYCMesh API Request Failed. getRequest({request_id})")
            raise
        except Exception:
            logger.exception(f"NYCMesh API Request Failed. getRequest({request_id})")
        return data

    def getNodes(self):
        try:
            data = self._get("/v1/nodes")
            if "error" in data:
                if "Not found" in data['error']:
                    raise ObjectDoesNotExist()
                else:
                    raise MeshApiException(data['error'])
        except requests.exceptions.RequestException:
            logger.exception("NYCMesh API Request Failed")
            raise
        except Exception:
            logger.exception("NYCMesh API Request Failed")

        return data

    def getNode(self, node_id):
        try:
            data = self._get(f"/v1/nodes/{node_id}")
            if "error" in data:
                if "Not found" in data['error']:
                    raise ObjectDoesNotExist()
                else:
                    raise MeshApiException(data['error'])
        except requests.exceptions.RequestException:
            logger.exception(f"NYCMesh API Request Failed. getNode({node_id})")
            raise
        except ObjectDoesNotExist:
            return self.getRequest(node_id)
        except Exception:
            logger.exception(f"NYCMesh API Request Failed. getNode({node_id})")
        return data

    def _get(self, path, params=None):
        """Return parsed objects returned from a GET request to ``path``.
        Parameters
        ----------
        path : str
            The path to fetch.
        params : dict
            The query parameters to add to the request (default:None).

        Returns
        -------
        data : dict
            Dictionary of request json
        """
        data = requests.get(f"{self.audience}{path}", params=params, headers=self.headers)
        return data.json()

    def _patch(self, path, data=None):
        """Return parsed objects returned from a PATCH request to ``path``.
        Parameters
        ----------
        path : str
            The path to fetch.
        data : dict
            Dictionary, bytes, or file-like object to send in the body
            of the request (default: None).

        Returns
        -------
        data : dict
            Dictionary of request json
        """
        data = requests.patch(f"{self.audience}{path}", data=data, headers=self.headers)
        return data.json()

    def _post(self, path, data=None, files=None, params=None):
        """Return parsed objects returned from a POST request to ``path``.
        Parameters
        ----------
        path : str
            The path to fetch.
        data : dict
            Dictionary, bytes, or file-like object to send in the body
            of the request (default: None).
        files : dict
            Dictionary, filename to file (like) object mapping (default: None).
        params : dict
            The query parameters to add to the request (default:None).

        Returns
        -------
        data : dict
            Dictionary of request json
        """
        data = requests.post(f"{self.audience}{path}", data=data or {}, params=params, headers=self.headers)
        return data.json()

    def _put(self, path, data=None):
        """Return parsed objects returned from a PUT request to ``path``.
        Parameters
        ----------
        path : str
            The path to fetch.
        data : dict
            Dictionary, bytes, or file-like object to send in the body
            of the request (default: None).

        Returns
        -------
        data : dict
            Dictionary of request json
        """
        data = requests.put(f"{self.audience}{path}", data=data, headers=self.headers)
        return data.json()
