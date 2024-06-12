import json
import os

def createSubDirs(path):
    parts = path.split('/') 
    

    for i in range(len(parts)):
        if '{' in parts[i] and '}' in parts[i]:
            parts[i] = f"{parts[i][1:-1]}-url" 

    new_path = '/'.join(parts)
    os.makedirs(new_path, exist_ok=True)




    return new_path 

def generate_next_js_routes(api_spec, output_dir='api'):
    paths = api_spec['paths']
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for route, methods in paths.items():

        try:
            print('route:', route)
            print('methods:', methods)

            total_path = output_dir + route

            total_path = createSubDirs(total_path)

            parts = total_path.split('/')
            for i in range(len(parts)):
                if '-url' in parts[i]:
                    parts[i] = "$" + "{" f"{parts[i][0:-4]}" + "}" 

            route = '/'.join(parts)

            # create route.ts file at end of path
            file_path = os.path.join(total_path, f'route.ts')

            print('file_path:', file_path)

            with open(file_path, 'w') as f:

                f.write(f'import {{ NextRequest, NextResponse }} from "next/server"; \n')
                f.write(f'import axios from "axios"; \n')
                f.write(f'import {{cookies}} from "next/headers"; \n')
                f.write(f'import {{ GalenClient }} from "@/lib/services/galen/client/GalenClient"; \n \n')

                f.write(f'const galenClient = GalenClient.getInstance(); \n')

                for method, details in methods.items():
                    summary = details.get('summary', '')
                    f.write(f'\n')
                    f.write(f'// {summary} \n')
                    f.write(f'export async function {method.upper()}(req: NextRequest, res: NextResponse) {{\n')
                    f.write(f'  try {{\n')

                    f.write(f'    const backendUrl = process.env.BACKEND_URL; \n')
                    f.write(f'    const config = {{ \n')
                    f.write(f'        headers: {{ \n')
                    f.write(f'       Authorization: "Bearer " + cookies().get("token")?.value \n')
                    f.write(f'        }} \n')
                    f.write(f'    }} \n')
                    f.write(f'    const newConfig = await galenClient.getExtraHeaders(config); \n')

                    params = details.get('parameters', [])
                    print('params:', params)
                    for param in params:
                        if isinstance(param, dict) and 'name' in param and 'in' in param:
                            name = param['name']
                            param_in = param['in']
                            param_required = param.get('required')   
                            if param_in == 'header':
                                f.write(f'    newConfig.headers["{name}"] = req.headers.get("{name}") || ""; \n')
                            elif param_in == 'path':
                                    f.write(f'    // Required URL parameter \n')
                                    f.write(f'    const {name} = req.nextUrl.searchParams.get("{name}"); \n')
                            else:
                                if param_required:
                                    f.write(f'    // Required query parameter \n')
                                    f.write(f'    newConfig.params["{name}"] = req.nextUrl.searchParams.get("{name}"); \n')
                                else:   
                                    f.write(f'    newConfig.params["{name}"] = req.nextUrl.searchParams.get("{name}") || ""; \n')

                    if method == 'get':
                        f.write(f'    const res = await axios.{method}(backendUrl + `{route}`, newConfig); \n')
                        f.write(f'    return NextResponse.json(res.data, {{ status: 200 }}); \n')
                    elif method == 'post' or method == 'put':
                        f.write(f'    const data = await req.json();\n')
                        f.write(f'    const res = await axios.{method}(backendUrl + `{route}`, data, newConfig); \n')
                        f.write(f'    return NextResponse.json(res.data, {{ status: 200 }}); \n')
                    elif method == 'delete':
                        f.write(f'    const res = await axios.{method}(backendUrl + `{route}`, newConfig); \n')
                        f.write(f'    return NextResponse.json(res.data, {{ status: 200 }}); \n')
                    
                    f.write(f'  }} catch (e: any) {{ \n')
                    f.write(f'    console.log("Error:", e) \n')
                    f.write(f'    return NextResponse.json({{ message: "Error {method}ing {parts[-1]}" }}, {{ status: e.response.status }}); \n')
                    f.write(f'  }} \n')
                    f.write(f'}} \n')

        except Exception as e:
            print('error:', e)
            # break

# Load the OpenAPI JSON file
with open('api-definition.json', 'r') as file:
    api_spec = json.load(file)

# Generate API routes
generate_next_js_routes(api_spec)
