import urllib.request
from urllib.parse import urlparse, urlunparse

# def canonize_url(url):
#     # Parse the URL into its components
#     parsed = urlparse(url)

#     # Normalize the scheme and hostname to lowercase
#     scheme = parsed.scheme.lower()
#     hostname = parsed.hostname.lower()

#     # Remove any default ports from the URL
#     if scheme == "http" and parsed.port == 80:
#         port = None
#     elif scheme == "https" and parsed.port == 443:
#         port = None
#     else:
#         port = parsed.port

#     # Reconstruct the normalized URL
#     canonical_url = urllib.parse.urlunparse((scheme, hostname, parsed.path, parsed.params, parsed.query, parsed.fragment))

#     # Add the port back if necessary
#     if port is not None:
#         canonical_url = urllib.parse.urlunparse((scheme, f"{hostname}:{port}", parsed.path, parsed.params, parsed.query, parsed.fragment))

#     return canonical_url

def canonize_url(url):
    parsed_url = urlparse(url)
    # Remove the fragment identifier from the URL
    parsed_url = parsed_url._replace(fragment='')
    # Make the hostname lowercase
    parsed_url = parsed_url._replace(netloc=parsed_url.netloc.lower())
    # Reconstruct the URL from its components
    canonized_url = urlunparse(parsed_url)
    return canonized_url