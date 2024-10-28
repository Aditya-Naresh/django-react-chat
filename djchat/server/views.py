from rest_framework import viewsets
from .models import Server
from .serializers import ServerSerializer
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, AuthenticationFailed
from django.db.models import Count
from .schema import server_list_docs


class ServerListViewSet(viewsets.ViewSet):
    """
    A ViewSet for listing and filtering `Server` objects based on query parameters. # noqa: 351

    Attributes:
        queryset (QuerySet): A QuerySet containing all server objects.
    """

    queryset = (
        Server.objects.all()
    )  # Fetches all server instances from the database.  # noqa: 351

    @server_list_docs
    def list(self, request):
        """
        Handles GET requests to retrieve a list of `Server` objects based on query parameters.  # noqa: 351

        Query Parameters:
            - category (str): Filter servers by category name.
            - qty (int): Limit the number of results returned.
            - by_user (bool): If 'true', filter servers by the authenticated user's membership.
            - by_serverid (int): Filter servers by a specific server ID.
            - with_num_members (bool): If 'true', include the number of members in the response.

        Returns:
            Response: A JSON response containing the serialized server data.

        Raises:
            AuthenticationFailed: If `by_user` is true and the user is not authenticated.
            ValidationError: If `by_serverid` is invalid or the server with the given ID is not found.
        """

        # Extract query parameters from the request URL
        queryset = self.queryset
        category = request.query_params.get(
            "category"
        )  # Category filter for servers.  # noqa: 351
        qty = request.query_params.get(
            "qty"
        )  # Limits the number of results returned.  # noqa: 351
        by_user = (
            request.query_params.get("by_user") == "true"
        )  # Check if filtering by the authenticated user. # noqa: 351
        by_server_id = request.query_params.get(
            "by_serverid"
        )  # Filter by specific server ID. # noqa: 351
        with_num_members = (
            request.query_params.get("with_num_members") == "true"
        )  # Include member count in response. # noqa: 351

        # Check if the user is authenticated when filtering by user
        if by_user and not request.user.is_authenticated:
            raise AuthenticationFailed(detail="User not logged in")

        # Apply category filter if the 'category' query parameter is provided
        if category:
            queryset = queryset.filter(category__name=category)

        # Filter servers by the authenticated user's membership if 'by_user' is true # noqa: 351
        if by_user:
            user_id = request.user.id
            queryset = queryset.filter(member=user_id)

        # Filter by server ID if 'by_serverid' is provided, with error handling
        if by_server_id:
            try:
                queryset = queryset.filter(id=by_server_id)
                # Raise error if no server matches the given ID
                if not queryset.exists():
                    raise ValidationError(
                        detail=f"Server with id {by_server_id} not found"
                    )
            except ValueError:
                raise ValidationError(
                    detail="Server Value Error"
                )  # Handle invalid server ID formats. # noqa: 351

        # Annotate the queryset with the number of members if 'with_num_members' is true # noqa: 351
        if with_num_members:
            queryset = queryset.annotate(num_members=Count("member"))

        # Limit the number of results if the 'qty' query parameter is provided
        if qty:
            queryset = queryset[: int(qty)]

        # Serialize the queryset into JSON format for the response
        serializer = ServerSerializer(
            queryset, many=True, context={"num_members": with_num_members}
        )

        # Return the serialized data as a JSON response
        return Response(serializer.data)
