from .main import check_admin


def attributes(request):
	return {
		'current_page': 'settings' if '/settings' == request.path else 'admin' if 'admin' in request.path else 'main',
		'is_admin': check_admin(request.user)
	}