import { CreateDataSourceSchema } from "@vbkg/schemas";
import { AppForm, CustomSheet, Button, toast } from "@vbkg/ui";
import { formCreateDataSourceConfig } from "../form/create";
import { useCreateDatasource } from "@vbkg/api-client";

export default function CreateDataSourceSheet() {
  const { mutate: createDatasource } = useCreateDatasource({
    onSuccess: () => {
      toast("Data source created successfully");
    },
    onError: (error) => {
      console.error("Error creating data source", error);
    },
  });
  return (
    <CustomSheet
      trigger={<Button variant="primary">Add Data Source</Button>}
      title="Add Data Source"
      description="Create a new data source configuration"
      side="right"
      size="lg"
    >
      <div className="px-4">
        <AppForm
          fields={formCreateDataSourceConfig}
          schema={CreateDataSourceSchema}
          watchFields={["source_type"]}
          onSubmit={(values) =>
            createDatasource({
              name: values.name,
              description: values.description,
              source_type: values.source_type,
              credentials: values.credentials
                ? Object.fromEntries(
                    values.credentials.map((credential) => [
                      credential.key,
                      credential.value,
                    ]),
                  )
                : undefined,
              connection_details: values.connection_details,
            })
          }
        />
      </div>
    </CustomSheet>
  );
}
